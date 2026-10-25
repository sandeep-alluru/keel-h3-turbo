#!/usr/bin/env python3
"""Build and run the MiniMax-H3 graph in ComfyUI over its HTTP API.

Why ComfyUI at all: the Motion Context node pack (latent-precise clip chaining) only exists as
ComfyUI nodes, and that is the measured fix for the 1.91x seam pop found in EXP-3. This script
drives the same graph the studio UI would, so chaining can be added without hand-driving the GUI.

Modes:
  --mode single   : one clip from first/last keyframes (baseline; proves the ComfyUI H3 path)
  --mode chain    : N spans chained through Motion Context Save/Load latent + Trim

Usage:
  h3_comfy.py --mode single --first kf0.png --last kf62.png --prompt-file p.json --out out.mp4
"""

import argparse
import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PRODUCTION = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# R2-M13: the host and the output root are CONFIGURED, not typed here. project.env
# (via h3env.sh) writes H3_COMFY_HOST / H3_OUTPUT_ROOT.
#
# R3-H2: there was ONE host setting spelled TWO ways - H3_COMFY_HOST and COMFY_HOST -
# and the configured one WON, so `--host http://127.0.0.1:8189` was silently replaced by
# the configured 8188 and the clip was rendered on the wrong GPU. There is now ONE
# variable: H3_COMFY_HOST. COMFY_HOST is retired; a caller that still sets it gets a
# loud refusal rather than a silent wrong host.
HOST = os.environ.get("H3_COMFY_HOST") or "http://127.0.0.1:8188"
if "COMFY_HOST" in os.environ and os.environ["COMFY_HOST"] != HOST:
    raise SystemExit(
        "[host] COMFY_HOST is retired (R3-H2). It is set to %r but H3_COMFY_HOST is %r. "
        "There is ONE host setting now; set H3_COMFY_HOST."
        % (os.environ["COMFY_HOST"], HOST))
OUT_LOCAL = (os.environ.get("H3_OUTPUT_ROOT") or os.environ.get("COMFY_OUT_LOCAL")
             or "output")

# R2-M13: the UNET is configured (H3_CHECKPOINT). The clip and the two VAEs keep
# their own names, also configurable, but they have one default each.
UNET_NAME = os.environ.get("H3_CHECKPOINT") or "minimax_h3_fl2va_fp8.safetensors"
CLIP_NAME = os.environ.get("H3_CLIP_NAME") or "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
VAE_NAME = os.environ.get("H3_VAE_NAME") or "minimax_h3_video_vae_fp16.safetensors"
AUDIO_VAE_NAME = os.environ.get("H3_AUDIO_VAE_NAME") or "minimax_h3_audio_vae_fp32.safetensors"

# AGENTS.md, section 5: the hard facts. A graph that violates them is refused here,
# before it is submitted, because a graph that validates can still fail (R1 lesson).
FRAME_GRID = 17          # the VAE grid is 17n+5
FRAME_CEILING = 345      # 14.375 s is the ceiling
MEMORY_ENVELOPE = 140    # (megapixels x frames) the envelope's upper bound


def check_hard_facts(width, height, frames, first_path, last_path):
    """Refuse the render when it breaks a fact AGENTS.md states. Returns nothing or exits.

    R2-L8: the renderer accepted 1281x700, 130 frames, the same still as first and
    last keyframe, and a None image in chain mode. Every one of those is a shot the
    production has already paid for. The check happens BEFORE the graph is built, so a
    refusal costs no GPU time.
    """
    if width % 32 or height % 32:
        raise SystemExit(f"[facts] {width}x{height}: the dimensions must be multiples of 32")
    if frames < 1 or (frames - 5) % FRAME_GRID != 0:
        raise SystemExit(f"[facts] {frames} frames: the VAE grid is 17n+5 "
                         f"(5, 22, 39, ... 124, 345)")
    if frames > FRAME_CEILING:
        raise SystemExit(f"[facts] {frames} frames: the ceiling is {FRAME_CEILING} (14.375 s)")
    mp_frames = (width * height * frames) / 1e6
    if mp_frames > MEMORY_ENVELOPE:
        raise SystemExit(f"[facts] {width}x{height}x{frames} = {mp_frames:.1f} MP*frames: "
                         f"the envelope is {MEMORY_ENVELOPE}")
    if first_path and last_path:
        if os.path.abspath(first_path) == os.path.abspath(last_path):
            raise SystemExit("[facts] the first and the last keyframe are the SAME FILE: "
                             "the model interpolates back to itself and the shot freezes")
        try:
            h1 = hashlib.sha256(open(first_path, "rb").read()).hexdigest()
            h2 = hashlib.sha256(open(last_path, "rb").read()).hexdigest()
            if h1 == h2:
                raise SystemExit("[facts] the first and the last keyframe are the SAME IMAGE "
                                 "(different path, identical content): the shot freezes")
        except OSError:
            pass   # unreadable: the upload below reports it
    return True


def upload_name(path, data=None):
    """The name a still is uploaded under: its CONTENT HASH.

    R3-C2: the file was uploaded under its BASENAME with overwrite=true, and every clip
    names its still S1.png ... S6.png. LoadImage reads the file when the job EXECUTES,
    not when it was queued, so three clip queues sharing one host overwrote each other's
    first frame: clip2/S1 was rendered from clip3's still and clip3/S1 from clip2's, and
    both were recorded as passes. A content-hash name cannot collide - the same still
    always lands on the same name, and two different stills never share one.
    """
    if data is None:
        data = open(path, "rb").read()
    digest = hashlib.sha256(data).hexdigest()[:12]
    ext = os.path.splitext(path)[1] or ".png"
    return "%s%s" % (digest, ext)


def upload(path):
    boundary = uuid.uuid4().hex
    data = open(path, "rb").read()
    name = upload_name(path, data)
    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'.encode(),
        f"Content-Type: {mimetypes.guess_type(path)[0] or 'image/png'}\r\n\r\n".encode(),
        data, b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n',
        f"--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(HOST + "/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())["name"]


def post(path, payload):
    req = urllib.request.Request(HOST + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=120).read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {path}: {body[:1500]}")


# ---- the TARGET host's catalogue (R3-M11)
#
# The two ComfyUI instances are NOT the same build: :8189 has no
# `ApplyMiniMaxH3FirstBlockCache` and has five LoRAs, :8188 has three and no
# `krea2_identity_edit_v2`. The LoRA check used to read the PRIMARY's models/loras
# directory whatever host the render was going to, and `check_graph` crashed with
# `KeyError: 'ApplyMiniMaxH3FirstBlockCache'` instead of reporting the missing node.
# Everything host-specific is now asked of the host the graph will be sent to.
_CATALOGUE = None


def object_info(host=None):
    """The node catalogue of the host we will submit to. Cached for this process."""
    global _CATALOGUE
    host = host or HOST
    if _CATALOGUE is None:
        with urllib.request.urlopen(host + "/object_info", timeout=120) as resp:
            _CATALOGUE = json.loads(resp.read())
    return _CATALOGUE


def missing_node_classes(graph, host=None):
    """The node classes the graph needs that the target host does not have.

    Returns [] when the catalogue cannot be read: a catalogue outage is not a
    missing node, and the render itself reports the real error.
    """
    try:
        info = object_info(host)
    except Exception as exc:
        print(f"[nodes] the catalogue of {host or HOST} is unreadable ({exc}); "
              f"the submit will report the error instead")
        return []
    missing = []
    for node_id, node in sorted(graph.items()):
        ctype = node.get("class_type")
        if ctype not in info:
            missing.append((node_id, ctype))
    return missing


def host_lora_names(host=None):
    """The LoRA files the target host's LoraLoader actually offers."""
    info = object_info(host)
    spec = info.get("LoraLoader")
    if not spec:
        return None
    required = spec.get("input", {}).get("required", {}) or {}
    combo = (required.get("lora_name") or [None])[0]
    return list(combo) if isinstance(combo, list) else None


# ---- the ONE stop check (R3-H1)
#
# The guard used to live only in the shell wrappers named in H3_RUN_PATH, so every GPU
# client - the thing that actually POSTs /prompt - bypassed it. The production's stop marker
# was on disk and the clip renders ran anyway. There is now ONE check, at the choke
# point every client goes through, and the lift is an explicit marker that
# NAMES the entry points allowed to run. The check itself lives in halt_guard.py, so
# the three clients cannot drift apart.
def require_not_halted(entry):
    """Refuse to submit when the production is stopped and nothing lifts this entry point."""
    from halt_guard import require_not_halted as _check
    return _check(entry)


# ---- the job this process owns (R3-H7)
#
# A killed client used to leave its job queued on the server: it still ran, still cost
# GPU minutes, and (with the upload race) still rendered against whatever still was
# current. Every submitted prompt id is remembered, and cancelled on every exit path.
_JOBS = []


def _cancel_job(prompt_id):
    """Remove a prompt from the server's queue - but only if it is still there.

    /interrupt stops whatever is RUNNING on the server, so it must never be sent for a
    job of ours that has already finished: by then another client's job may be running.
    """
    try:
        q = json.loads(urllib.request.urlopen(HOST + "/queue", timeout=30).read())
    except Exception:
        return
    running = [t[1] for t in q.get("queue_running", []) if isinstance(t, list)]
    pending = [t[1] for t in q.get("queue_pending", []) if isinstance(t, list)]
    if prompt_id in running:
        try:
            urllib.request.urlopen(urllib.request.Request(
                HOST + "/interrupt", data=b"{}", headers={"Content-Type": "application/json"}),
                timeout=30).read()
        except Exception:
            pass
    if prompt_id in running or prompt_id in pending:
        try:
            urllib.request.urlopen(urllib.request.Request(
                HOST + "/queue", data=json.dumps({"delete": [prompt_id]}).encode(),
                headers={"Content-Type": "application/json"}), timeout=30).read()
        except Exception:
            pass


def _cancel_all_jobs():
    for pid in list(_JOBS):
        _cancel_job(pid)
    _JOBS[:] = []


def _on_signal(signum, frame):
    # Turn a signal into a normal exit, so atexit runs and the job is cancelled.
    raise SystemExit(128 + signum)


def _install_exit_handlers():
    import atexit
    import signal
    atexit.register(_cancel_all_jobs)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(sig, _on_signal)
        except (ValueError, OSError, AttributeError):
            pass


def fetch(meta, dest_dir):
    """Download a ComfyUI output file to the local output tree (works for remote hosts too).

    ComfyUI's output directory is usually created by root (it writes as root inside its container), so a direct
    write can fail with EACCES. Stage in a PRIVATE temp directory (R2-M8: /tmp/<filename> collides
    across machines and across two runs of the same file) and copy into place.

    R2-M8: this used to swallow every failure - the caller printed "fetch failed" and carried on
    as if the render had been saved. A render that was not saved is a failure, and it now raises.
    """
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, meta["filename"])
    url = (f"{HOST}/view?filename={urllib.parse.quote(meta['filename'])}"
           f"&subfolder={urllib.parse.quote(meta.get('subfolder') or '')}&type=output")
    staged_dir = tempfile.mkdtemp(prefix="h3-fetch-")
    staged = os.path.join(staged_dir, meta["filename"])
    try:
        with urllib.request.urlopen(url, timeout=600) as resp, open(staged, "wb") as fh:
            fh.write(resp.read())
        try:
            os.replace(staged, dest)
        except OSError:
            # output directory belongs to root: copy it in, and CHECK the copy.
            import subprocess
            cp = subprocess.run(["sudo", "cp", staged, dest], check=False)
            if cp.returncode != 0:
                raise RuntimeError(f"sudo cp into {dest} failed with {cp.returncode}")
            ch = subprocess.run(["sudo", "chown", f"{os.getuid()}:{os.getgid()}", dest],
                                check=False)
            if ch.returncode != 0:
                raise RuntimeError(f"sudo chown of {dest} failed with {ch.returncode}")
        if not os.path.isfile(dest) or os.path.getsize(dest) == 0:
            raise RuntimeError(f"{dest} did not arrive (zero bytes)")
        return dest
    finally:
        shutil.rmtree(staged_dir, ignore_errors=True)


def run(graph, label, timeout=3600):
    # RC-H1: the stop check is HERE, in the function every submitter reaches. It used
    # to be in main() only - so h3_comfy_ctrl.py, which calls run() directly, submitted
    # its jobs with NO check at all while the production's stop marker was on disk. The name
    # looked up is the one the caller passes; the environment is only a fallback.
    require_not_halted(os.environ.get("H3_ENTRY_POINT") or "h3_comfy.py")
    # RC-M2: the exit handlers are installed HERE, in the function every submitter
    # reaches. They used to be installed in main() only, so a caller that called
    # run() directly - h3_comfy_ctrl.py does - had no cancel-on-exit at all, and a
    # job of its own kept running on the server after the process was killed.
    _install_exit_handlers()
    # R3-M11: the graph is checked against the TARGET host's catalogue before it is
    # queued. :8189 has no ApplyMiniMaxH3FirstBlockCache, so `--accelerate` there
    # used to be accepted and then died inside ComfyUI with a KeyError.
    missing = missing_node_classes(graph)
    if missing:
        raise SystemExit(
            "[nodes] %s does not have: %s. The render would fail inside ComfyUI; "
            "the graph was not queued."
            % (HOST, ", ".join("%s (%s)" % (node_id, ctype) for node_id, ctype in missing)))
    pid = post("/prompt", {"prompt": graph, "client_id": uuid.uuid4().hex})["prompt_id"]
    _JOBS.append(pid)
    started = time.time()
    while time.time() - started < timeout:
        hist = json.loads(urllib.request.urlopen(HOST + f"/history/{pid}", timeout=120).read())
        if pid in hist:
            entry = hist[pid]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                raise SystemExit(f"[{label}] comfy error: {json.dumps(status)[:800]}")
            videos = []
            for out in entry.get("outputs", {}).values():
                for key in ("images", "videos", "gifs", "audio"):
                    videos += [v for v in out.get(key, []) if isinstance(v, dict) and v.get("filename")]
            print(f"[{label}] done in {time.time() - started:.1f}s -> {[v.get('filename') for v in videos]}")
            if not videos:
                raise SystemExit(f"[{label}] comfy reported no output file")
            for meta in videos:
                # R2-M8: a fetch that fails is a failure of the RENDER, not a message.
                local = fetch(meta, os.path.join(OUT_LOCAL, meta.get("subfolder") or ""))
                print(f"[{label}] saved {local}")
                # R3-L9: the caller used to GUESS where the file was (a "_00001_" name,
                # then the first sorted match), which picked up a stale file. It reads
                # the real path from this line instead.
                print(f"SAVED {local}")
            return pid, videos
        time.sleep(3)
    raise SystemExit(f"[{label}] timeout")


def _model_chain(graph, unet_ref, clip_ref, lora, lora_strength, accelerate):
    """Wire the UNET -> (sage) -> (block cache) -> (lora) -> sigma-shift chain.

    R2-H5: `--lora` and `--accelerate` were parsed and then dropped on the floor, so a
    "LoRA run" was not a LoRA run and an "accelerated run" was not accelerated, and
    nothing said so. Both flags now put a node in the graph, or they are refused.

    R3-M11: LoraLoader returns (MODEL, CLIP). The CLIP output was never wired, so
    `strength_clip` did nothing at all - the text encoder was the un-patched one.
    The returned CLIP ref is now what feeds the prompt encoder when a LoRA is used.

    Returns the node id that carries the MODEL and the one that carries the CLIP.
    """
    model_ref = unet_ref
    clip_out = clip_ref
    if accelerate:
        graph["20"] = {"class_type": "MiniMaxH3MemoryEfficientSageAttentionPatch",
                       "inputs": {"model": model_ref}}
        model_ref = ["20", 0]
        graph["21"] = {"class_type": "ApplyMiniMaxH3FirstBlockCache",
                       "inputs": {"model": model_ref, "mode": "H3 Fast — 0.10 / max 2",
                                  "threshold": 0.1, "start_percent": 0.1, "end_percent": 0.95,
                                  "max_consecutive_hits": 2, "temporal_guard": False}}
        model_ref = ["21", 0]
    if lora:
        graph["22"] = {"class_type": "LoraLoader",
                       "inputs": {"model": model_ref, "clip": clip_ref, "lora_name": lora,
                                  "strength_model": lora_strength, "strength_clip": lora_strength}}
        model_ref = ["22", 0]
        clip_out = ["22", 1]
    return model_ref, clip_out


def base_graph(first_name, last_name, prompt, steps, seed, width, height, frames, prefix,
               lora=None, lora_strength=1.0, accelerate=False):
    """last_name may be None -> true I2VA (first frame only). Pinning the SAME still to both ends makes the
    model interpolate back to itself and suppresses motion; that mistake produced twelve near-static shots.

    R2-H5: `last_name` used to be accepted and then ignored, so `--last` in single mode was
    a first-frame-only render wearing FL2VA's name. It is wired now: the graph carries
    `last_frame` whenever a last frame was given.
    """
    graph = {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": UNET_NAME, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": CLIP_NAME, "type": "minimax"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE_NAME}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE_NAME}},
        "5": {"class_type": "LoadImage", "inputs": {"image": first_name}},
    }
    i2v = {"clip": ["2", 0], "vae": ["3", 0], "prompt": prompt, "width": width,
           "height": height, "length": frames, "first_frame": ["5", 0]}
    if last_name:
        graph["6"] = {"class_type": "LoadImage", "inputs": {"image": last_name}}
        i2v["last_frame"] = ["6", 0]
    graph["7"] = {"class_type": "MiniMaxH3ImageToVideo", "inputs": i2v}
    model_ref, clip_ref = _model_chain(graph, ["1", 0], ["2", 0], lora, lora_strength, accelerate)
    if lora:
        # R3-M11: the LoRA's CLIP now feeds the prompt encoder.
        i2v["clip"] = clip_ref
    graph["8"] = {"class_type": "MiniMaxH3SigmaShift",
                  "inputs": {"model": model_ref, "shift_video": 12.0, "shift_audio": 3.0}}
    graph["9"] = {"class_type": "KSampler",
                  "inputs": {"model": ["8", 0], "positive": ["7", 0], "negative": ["7", 0],
                             "latent_image": ["7", 1], "seed": seed, "steps": steps, "cfg": 1.0,
                             "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}}
    graph["10"] = {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["3", 0]}}
    graph["11"] = {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["9", 0], "vae": ["4", 0]}}
    graph["12"] = {"class_type": "CreateVideo",
                   "inputs": {"images": ["10", 0], "fps": 24.0, "audio": ["11", 0]}}
    graph["13"] = {"class_type": "SaveVideo",
                   "inputs": {"video": ["12", 0], "filename_prefix": prefix, "format": "auto"}}
    return graph




def chain_graph(first_name, last_name, prompt, steps, seed, width, height, frames, prefix,
                load_index, save_index, has_first=True, has_last=True,
                lora=None, lora_strength=1.0, accelerate=False):
    """One span of a chain: the previous clip's latent tail is pinned into this clip."""
    graph = {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": UNET_NAME, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": CLIP_NAME, "type": "minimax"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE_NAME}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE_NAME}},
        "16": {"class_type": "MiniMaxH3MotionContextLoadLatent",
               "inputs": {"latent_path": "h3ctx", "clip_index": load_index, "stock_format": False,
                          "folder": "output"}},
    }
    i2v = {"clip": ["2", 0], "vae": ["3", 0], "prompt": prompt, "width": width,
           "height": height, "length": frames}
    if has_first:
        if not first_name:
            raise SystemExit("[facts] chain mode was asked for a first frame and given none")
        graph["5"] = {"class_type": "LoadImage", "inputs": {"image": first_name}}
        i2v["first_frame"] = ["5", 0]
    if has_last:
        if not last_name:
            raise SystemExit("[facts] chain mode was asked for a last frame and given none")
        graph["6"] = {"class_type": "LoadImage", "inputs": {"image": last_name}}
        i2v["last_frame"] = ["6", 0]
    graph["7"] = {"class_type": "MiniMaxH3ImageToVideo", "inputs": i2v}
    model_ref, clip_ref = _model_chain(graph, ["1", 0], ["2", 0], lora, lora_strength, accelerate)
    if lora:
        # R3-M11: the LoRA's CLIP now feeds the prompt encoder.
        i2v["clip"] = clip_ref
    graph["8"] = {"class_type": "MiniMaxH3MotionContext",
                  "inputs": {"conditioning": ["7", 0], "vae": ["3", 0], "latent": ["7", 1],
                             "context_length": "22", "audio_context_length": 18,
                             "context_latent": ["16", 0]}}
    graph["9"] = {"class_type": "MiniMaxH3SigmaShift",
                  "inputs": {"model": model_ref, "shift_video": 12.0, "shift_audio": 3.0}}
    graph["10"] = {"class_type": "KSampler",
                   "inputs": {"model": ["9", 0], "positive": ["8", 0], "negative": ["8", 0],
                              "latent_image": ["7", 1], "seed": seed, "steps": steps, "cfg": 1.0,
                              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}}
    graph["11"] = {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["3", 0]}}
    graph["12"] = {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["10", 0], "vae": ["4", 0]}}
    graph["13"] = {"class_type": "MiniMaxH3MotionContextTrim",
                   "inputs": {"images": ["11", 0], "trim_frames": ["8", 1], "audio": ["12", 0],
                              "fps": 24.0, "match_tail": True}}
    graph["14"] = {"class_type": "CreateVideo",
                   "inputs": {"images": ["13", 0], "fps": 24.0, "audio": ["13", 1]}}
    graph["15"] = {"class_type": "SaveVideo",
                   "inputs": {"video": ["14", 0], "filename_prefix": prefix, "format": "auto"}}
    graph["17"] = {"class_type": "MiniMaxH3MotionContextSaveLatent",
                   "inputs": {"latent": ["10", 0], "filename_prefix": "h3ctx/clip",
                              "clip_index": save_index}}
    return graph


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="single", choices=["single", "chain", "extend"])
    ap.add_argument("--spans", type=int, default=2)
    ap.add_argument("--first", required=True)
    ap.add_argument("--last", default=None, help="omit for I2VA (first-frame only)")
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--steps", type=int, default=16)
    ap.add_argument("--seed", type=int, default=2511)
    ap.add_argument("--width", type=int, default=704)
    ap.add_argument("--height", type=int, default=1280)
    ap.add_argument("--frames", type=int, default=124)
    ap.add_argument("--prefix", default="h3comfy/single")
    ap.add_argument("--accelerate", action="store_true", help="Sage attention + FirstBlockCache")
    ap.add_argument("--lora", default=None, help="LoRA filename in ComfyUI models/loras")
    ap.add_argument("--lora-strength", type=float, default=1.0)
    args = ap.parse_args()

    # R3-H1: the ONE check, before anything is uploaded or submitted. The production's stop
    # marker is set by the project lead; a LIFT marker names the entry points allowed to run anyway.
    _install_exit_handlers()
    # RC-H1: the name looked up is the ENTRY POINT THAT WAS INVOKED - the caller
    # passes it down in H3_ENTRY_POINT - and this client's own name is only the
    # fallback. It used to pass its own name, which worked only because the guard
    # preferred the environment; with the explicit argument winning, the clip path's
    # lift stopped matching and every clip render was refused as "h3_comfy.py did not
    # start".
    require_not_halted(os.environ.get("H3_ENTRY_POINT") or "h3_comfy.py")

    # R2-L8: the hard facts are checked BEFORE anything is uploaded or submitted.
    check_hard_facts(args.width, args.height, args.frames, args.first, args.last)

    # R3-M11: a LoRA that is not THERE is a refusal, not a silent no-op - and "there"
    # is now the TARGET host's list, not the primary's models/loras directory.
    # :8188 offers 3 LoRAs, :8189 offers 5; the old check read one host's directory
    # whatever host the render was going to.
    if args.lora:
        names = host_lora_names()
        if names is None:
            raise SystemExit(f"[lora] {HOST} does not offer a LoraLoader node")
        if args.lora not in names:
            raise SystemExit("[lora] %s is not on %s. It offers: %s"
                             % (args.lora, HOST, ", ".join(names)))

    prompt = json.load(open(args.prompt_file))["prompt"]
    first = upload(args.first)
    last = upload(args.last) if args.last else None
    print(f"[upload] {first} / {last or '(none: I2VA first-frame only)'}")

    if args.mode == "extend":
        # continuous take: span 0 starts from the keyframe, later spans continue from the pinned
        # latent tail alone (no keyframes), which is the only way H3 can exceed 14.4 s.
        results = []
        for span in range(args.spans):
            graph = chain_graph(first, last, prompt, args.steps, args.seed,
                                args.width, args.height, args.frames,
                                f"{args.prefix}_e{span}", span, span + 1,
                                has_first=(span == 0), has_last=False,
                                lora=args.lora, lora_strength=args.lora_strength,
                                accelerate=args.accelerate)
            pid, videos = run(graph, f"extend{span}")
            results.append({"span": span, "prompt_id": pid, "videos": videos})
            print(f"[extend] span {span} done: {videos[0]['filename'] if videos else 'none'}")
        print(json.dumps(results, indent=2))
        return

    if args.mode == "single":
        graph = base_graph(first, last, prompt, args.steps, args.seed,
                           args.width, args.height, args.frames, args.prefix,
                           lora=args.lora, lora_strength=args.lora_strength,
                           accelerate=args.accelerate)
        pid, videos = run(graph, "single")
        print(json.dumps({"prompt_id": pid, "videos": videos}, indent=2))
        return

    results = []
    for span in range(args.spans):
        graph = chain_graph(first, last, prompt, args.steps, args.seed,
                            args.width, args.height, args.frames,
                            f"{args.prefix}_s{span}", span, span + 1, has_first=(span == 0),
                            lora=args.lora, lora_strength=args.lora_strength,
                            accelerate=args.accelerate)
        pid, videos = run(graph, f"span{span}")
        results.append({"span": span, "prompt_id": pid, "videos": videos})
        print(json.dumps(results[-1], indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
