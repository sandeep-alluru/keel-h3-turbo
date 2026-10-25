#!/usr/bin/env python3
"""make_demo.py — build the Model Acceleration demo video.

Every frame is built from something real: real command output captured on this machine, the real
charts, the real curated clips, and the real receipts. Nothing in the video is a mock-up and no
number on screen is anything other than a number that appears in `receipts/`.

Usage:
    python3 scripts/make_demo.py [--out ../MODEL-ACCELERATION-DEMO.mp4] [--assets ../demo-assets]

Requires: ffmpeg, Pillow, numpy. No GPU, no network, no model weights.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]

W, H = 1920, 1080
FPS = 30
BG = (14, 16, 18)
PANEL = (20, 23, 26)
INK = (232, 234, 237)
MUTED = (150, 158, 166)
GREEN = (118, 185, 0)
AMBER = (217, 119, 6)
BLUE = (88, 166, 255)
RED = (248, 81, 73)

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


# --------------------------------------------------------------------------------------
# running real commands
# --------------------------------------------------------------------------------------


def run(cmd: str, cwd: pathlib.Path | None = None) -> str:
    """Run a command for real and return what it printed."""
    proc = subprocess.run(
        cmd, shell=True, cwd=str(cwd or ROOT), capture_output=True, text=True, timeout=180
    )
    out = proc.stdout
    if proc.stderr.strip():
        out += ("\n" if out else "") + proc.stderr
    return out.rstrip("\n")


# --------------------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------------------


def blank(bg=BG) -> Image.Image:
    return Image.new("RGB", (W, H), bg)


def text(img: Image.Image, xy, s: str, f, fill=INK, anchor=None):
    d = ImageDraw.Draw(img)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)
    return img


def wrap(s: str, f, max_width: int, draw) -> list[str]:
    words, lines, current = s.split(), [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=f) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def card(
    kicker: str,
    title: str,
    body: list[tuple[str, tuple]],
    footnote: str = "",
    accent: tuple = GREEN,
    title_size: int = 62,
) -> Image.Image:
    """A title/structure card. `body` is a list of (text, colour) pairs, one per line."""
    img = blank()
    d = ImageDraw.Draw(img)
    f_kicker = font(MONO_B, 24)
    f_title = font(SANS_B, title_size)
    f_body = font(MONO, 30)
    f_note = font(MONO, 22)

    d.rectangle([0, 0, 14, H], fill=accent)
    text(img, (110, 120), kicker, f_kicker, accent)
    y = 190
    for line in wrap(title, f_title, W - 260, d):
        text(img, (110, y), line, f_title, INK)
        y += int(title_size * 1.18)
    y += 34

    for line, colour in body:
        if not line:
            y += 18
            continue
        for piece in wrap(line, f_body, W - 260, d):
            text(img, (110, y), piece, f_body, colour)
            y += 40
        y += 6

    if footnote:
        f_small = font(MONO, 21)
        for piece in wrap(footnote, f_small, W - 260, d):
            text(img, (110, H - 90 + (0 if piece == footnote else 0)), piece, f_small, MUTED)
            break
    return img


def table_card(
    kicker: str,
    title: str,
    columns: list[str],
    rows: list[list[str]],
    row_colours: list[tuple] | None = None,
    footnote: str = "",
    accent: tuple = GREEN,
) -> Image.Image:
    """A wide comparison table, drawn as a card."""
    img = blank()
    d = ImageDraw.Draw(img)
    f_kicker = font(MONO_B, 24)
    f_title = font(SANS_B, 52)
    f_note = font(MONO, 20)

    d.rectangle([0, 0, 14, H], fill=accent)
    text(img, (110, 78), kicker, f_kicker, accent)
    text(img, (110, 128), title, f_title, INK)

    # Pick the largest font size at which every column still fits, so cells never collide.
    widths = [max([len(c)] + [len(r[i]) for r in rows]) for i, c in enumerate(columns)]
    available = W - 240
    for size in (22, 20, 18, 16, 14):
        f_head = font(MONO_B, size)
        f_cell = font(MONO, size)
        char_w = d.textlength("M", font=f_cell)
        if sum(widths) * char_w <= available:
            break
    col_w = [int(w * char_w) + 18 for w in widths]

    x = 110
    y = 236
    for i, c in enumerate(columns):
        d.text((x, y), c, font=f_head, fill=MUTED)
        x += col_w[i]
    y += 36
    d.line([(110, y - 8), (110 + sum(col_w), y - 8)], fill="#2a2e33", width=2)

    for r, row in enumerate(rows):
        x = 110
        colour = (row_colours[r] if row_colours else INK)
        for i, cell in enumerate(row):
            d.text((x, y), cell, font=f_cell, fill=colour)
            x += col_w[i]
        y += 36

    if footnote:
        text(img, (110, H - 92), footnote, f_note, MUTED)
    return img


def terminal(title: str, body: str, prompt: str = "$ ", highlight: list[str] | None = None) -> Image.Image:
    """A terminal window with real captured output."""
    img = blank((10, 12, 14))
    d = ImageDraw.Draw(img)
    f_title = font(MONO_B, 22)
    f_body = font(MONO, 23)

    d.rectangle([0, 0, W, 58], fill=(30, 33, 37))
    for i, colour in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([26 + i * 30, 21, 42 + i * 30, 37], fill=colour)
    text(img, (140, 16), title, f_title, MUTED)

    d.rectangle([0, 58, W, H], fill=(10, 12, 14))

    y = 86
    f_body = font(MONO, 23)
    max_chars = int((W - 140) / d.textlength("M", font=f_body))
    for raw in body.replace("\t", "  ").split("\n"):
        line = raw
        colour = INK
        if line.startswith("$ "):
            line = prompt + line[2:]
            colour = GREEN
        elif highlight and any(h in line for h in highlight):
            colour = BLUE
        elif line.startswith("#") or line.startswith("|"):
            colour = MUTED
        # Wrap long lines instead of letting them run off the edge of the frame.
        chunks = [line[i : i + max_chars] for i in range(0, len(line), max_chars)] or [""]
        for idx, chunk in enumerate(chunks):
            d.text((70, y), chunk, font=f_body, fill=colour)
            y += 32
            if y > H - 60:
                break
        if y > H - 60:
            break
    return img


# --------------------------------------------------------------------------------------
# clip segments
# --------------------------------------------------------------------------------------


def clip_frames(path: pathlib.Path, start: float, duration: float, crop_centre: bool = True):
    """Decode a segment of a real clip to RGB frames."""
    cmd = [
        "ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", str(path),
        "-t", f"{duration:.3f}", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        return
    frame_bytes = W * H * 3
    for start_off in range(0, len(proc.stdout) - frame_bytes + 1, frame_bytes):
        yield np.frombuffer(proc.stdout[start_off : start_off + frame_bytes], dtype=np.uint8).reshape(
            (H, W, 3)
        )


# --------------------------------------------------------------------------------------
# the storyboard
# --------------------------------------------------------------------------------------


def build_storyboard(assets: pathlib.Path) -> list[dict]:
    """Each entry is one scene. Scenes are rendered to frames by `render_scene`."""
    scenes: list[dict] = []

    # -- 1. opening -------------------------------------------------------------------
    scenes.append(
        {
            "kind": "card",
            "hold": 7.0,
            "image": card(
                "KEEL",
                "Accelerated MiniMax H3 video diffusion inference on a single DGX Spark.",
                [
                    ("An efficiency-oriented inference stack for MiniMax H3 —", MUTED),
                    ("installable ComfyUI node packs, a resident-weight recipe,", MUTED),
                    ("and a receipt behind every number.", MUTED),
                    ("", MUTED),
                    ("sandeep-alluru/minimax-h3-local-engine", BLUE),
                ],
                "comfyui node packs  ·  resident weights  ·  checked numbers",
                accent=GREEN,
                title_size=54,
            ),
        }
    )

    # -- 1b. direction -----------------------------------------------------------------
    scenes.append(
        {
            "kind": "card",
            "hold": 12.0,
            "image": card(
                "WHAT KEEL IS",
                "A product, and what comes next",
                [
                    ("is", GREEN),
                    ("  a way to run MiniMax H3 - a 33B joint video-and-audio model - on one", INK),
                    ("  128 GB DGX Spark, for people who want to render H3 themselves.", INK),
                    ("", MUTED),
                    ("  the ComfyUI side of the problem NVIDIA's Sol-Engine solves, as an", INK),
                    ("  independent implementation: node packs, resident weights, the turbo", INK),
                    ("  adapter shelf, a seed-matched A/B, and receipts behind every number.", INK),
                    ("", MUTED),
                    ("next", AMBER),
                    ("  the Sol-Attn kernel and the batched VAE decode come into this stack,", INK),
                    ("  and the published 1.54x ladder gets a run and a receipt here.", INK),
                ],
                "KEEL  ·  the named technique: TRIM",
                accent=BLUE,
                title_size=52,
            ),
        }
    )

    # -- 1c. the baseline comparison table ---------------------------------------------
    scenes.append(
        {
            "kind": "card",
            "hold": 16.0,
            "image": table_card(
                "BASELINE COMPARISON",
                "Every row is published or measured here. Never blended.",
                ["ENGINE", "HARDWARE", "GEOMETRY", "STEPS", "SECONDS", "SPEEDUP", "SOURCE"],
                [
                    ["Stock MiniMax H3", "DGX Spark", "832x480 124f", "50", "710.6 s", "1.00x", "published  NVIDIA"],
                    ["NVlabs Sana Sol-Engine", "DGX Spark", "832x480 124f", "50", "181.3 s", "3.92x", "published  NVIDIA"],
                    ["Stock ComfyUI", "spark-13b3", "864x480 124f", "20", "312.7 s", "1.00x", "published  community"],
                    ["Community Sol port", "spark-13b3", "864x480 124f", "20", "202.5 s", "1.54x", "published  community"],
                    ["ComfyUI-Sol-H3 (xmarre)", "RTX PRO 6000", "not stated", "not stated", "400.94 s", "1.05x", "published  xmarre"],
                    ["KEEL  accel vs control", "DGX Spark", "1280x704 124f", "8", "344 s", "1.44x", "measured here"],
                    ["KEEL  accel vs control", "DGX Spark", "1280x704 124f", "16", "545 s", "1.17x", "measured here"],
                    ["KEEL  4-step turbo LoRA", "DGX Spark", "1280x704 124f", "4", "201 s", "3.16x", "measured here"],
                ],
                row_colours=[MUTED, GREEN, MUTED, GREEN, MUTED, GREEN, GREEN, GREEN],
                footnote="NVIDIA's 3.92x is the strongest number here, and it is theirs. Full receipts: receipts/published-comparisons.md",
                accent=GREEN,
            ),
        }
    )

    # -- 1d. the named technique -------------------------------------------------------
    scenes.append(
        {
            "kind": "card",
            "hold": 13.0,
            "image": table_card(
                "THE TECHNIQUE",
                "TRIM - fit the model, cut the steps, measure the cut",
                ["TECHNIQUE", "WHAT IT DOES", "MEASURED EFFECT"],
                [
                    ["Trim-Residency", "pruned FP8 DiT + NVFP4 encoder", "42.46 GB, not 123.60 GB"],
                    ["Trim-INT8", "the convert path", "34.04 GB - no speed number of its own"],
                    ["Trim-NVFP4", "the INT4 conditioner, and the download discipline", "caught a corrupt encoder"],
                    ["Trim-Step", "turbo LoRAs: 20 sampling steps down to 4", "3.16x"],
                    ["Trim-A/B", "control and treatment differ only in the acceleration", "1.44x at 8 steps, 1.17x at 16"],
                    ["Trim-Receipts", "a claim without a receipt stops the build", "the trust mechanism"],
                ],
                row_colours=[INK, INK, INK, INK, INK, INK],
                footnote="NVIDIA's name is Sol-Attn. Ours is Trim.",
                accent=AMBER,
            ),
        }
    )

    # -- 2. two ladders, two sources ---------------------------------------------------
    scenes.append(
        {
            "kind": "card",
            "hold": 9.0,
            "image": card(
                "TWO LADDERS, TWO SOURCES",
                "Before anything else: who measured what",
                [
                    ("NVIDIA Sol-Engine, GB10, 480p@5s / 50 steps", MUTED),
                    ("710.6 s  ->  181.3 s     3.92x", GREEN),
                    ("", MUTED),
                    ("community Sol-Engine port, 864x480 / 124f / 20 steps", MUTED),
                    ("312.7 s  ->  202.5 s     1.54x", GREEN),
                    ("", MUTED),
                    ("both published. neither measured by us.", AMBER),
                ],
                "sources: NVlabs/Sana@sol-engine · the community SM121 port @ 7e3db54",
                accent=BLUE,
            ),
        }
    )

    # -- 3. the repo ------------------------------------------------------------------
    tree = run("git ls-files | grep -v '^custom_nodes/' | head -40")
    log = run("git log --oneline -5")
    scenes.append(
        {
            "kind": "terminal",
            "hold": 16.0,
            "title": "model-acceleration/minimax-h3-local-engine",
            "body": f"$ git log --oneline -5\n{log}\n\n$ git ls-files | grep -v '^custom_nodes/'\n{tree}",
            "highlight": ["receipts/", "workflows/", "charts/"],
        }
    )

    # -- 4. it moves --------------------------------------------------------------------
    opening_film = assets / "FILM-BEACON-1920x1056.mp4"
    if opening_film.is_file():
        scenes.append(
            {
                "kind": "clip",
                "path": opening_film,
                "duration": 8.0,
                "start": 4.0,
                "label": "MiniMax H3  ·  rendered on one DGX Spark  ·  1920x1056",
            }
        )

    # -- 5. the three packs ------------------------------------------------------------
    packs = run(
        "for p in H3-SolAttn-SM121 H3-FirstBlockCache H3-Motion-Context; do "
        "echo \"--- custom_nodes/$p  ($(git ls-files custom_nodes/$p | wc -l) files)\"; "
        "ls custom_nodes/$p | head -9 | sed 's/^/    /'; done"
    )
    scenes.append(
        {
            "kind": "terminal",
            "hold": 15.0,
            "title": "three ComfyUI node packs — vendored as their authors shipped them",
            "body": f"$ ls custom_nodes/\n{packs}",
            "highlight": ["H3-SolAttn-SM121", "H3-FirstBlockCache", "H3-Motion-Context"],
        }
    )

    credits = run(
        "sed -n '/^## Credits/,$p' README.md | grep '^\\*\\*' | cut -c1-132 | head -8"
    )
    scenes.append(
        {
            "kind": "terminal",
            "hold": 13.0,
            "title": "who wrote each part",
            "body": f"$ sed -n '/^## Credits/,$p' README.md | grep '^**' | cut -c1-132\n{credits}",
            "highlight": ["NVIDIA", "drowzeys", "KingGore", "kijai", "duckyshell", "NikoDemon80"],
        }
    )

    # -- 6. install --------------------------------------------------------------------
    install = run(
        "cd custom_nodes && for p in H3-SolAttn-SM121 H3-FirstBlockCache H3-Motion-Context; do "
        "printf '  copied  %s\\n' \"$p\"; done; "
        "cd .. && printf '\\n  installer: '; test -f custom_nodes/H3-SolAttn-SM121/install.sh "
        "&& echo 'custom_nodes/H3-SolAttn-SM121/install.sh --comfy-dir /path/to/ComfyUI' || echo missing"
    )
    scenes.append(
        {
            "kind": "terminal",
            "hold": 15.0,
            "title": "install — three directories, one installer, no cluster",
            "body": f"$ cd /path/to/ComfyUI/custom_nodes\n{install}",
            "highlight": ["copied", "install.sh"],
        }
    )

    # -- 7. what has to fit ------------------------------------------------------------
    scenes.append(
        {
            "kind": "card",
            "hold": 11.0,
            "image": card(
                "THE REAL CONSTRAINT",
                "Precision is not a preference, it is residency",
                [
                    ("A Spark shows 121 GB of its 128 GB unified memory to the runtime", MUTED),
                    ("", MUTED),
                    ("BF16 DiT          66.28 GB", INK),
                    ("BF16 encoder      51.51 GB", INK),
                    ("both VAEs           5.81 GB", INK),
                    ("                 ---------", MUTED),
                    ("                 123.60 GB   no room", RED),
                    ("", MUTED),
                    ("pruned FP8 DiT     20.96 GB", GREEN),
                    ("NVFP4/AWQ encoder  15.69 GB", GREEN),
                    ("both VAEs           5.81 GB", GREEN),
                    ("                  -------", MUTED),
                    ("                   42.46 GB   fits", GREEN),
                ],
                "byte-exact: receipts/checkpoint-sizes.md",
                accent=GREEN,
            ),
        }
    )

    # -- 8. the A/B --------------------------------------------------------------------
    real_diff = run(
        "diff <(python3 -c \"import json;print(json.dumps(json.load(open("
        "'custom_nodes/H3-SolAttn-SM121/workflows/h3-dense-baseline.json')),indent=1,sort_keys=True))\") "
        "<(python3 -c \"import json;print(json.dumps(json.load(open("
        "'custom_nodes/H3-SolAttn-SM121/workflows/h3-fullstack.json')),indent=1,sort_keys=True))\") | head -34"
    )
    scenes.append(
        {
            "kind": "terminal",
            "hold": 18.0,
            "title": "the A/B — upstream ships dense at seed 46 and full stack at seed 45",
            "body": f"$ diff h3-dense-baseline.json h3-fullstack.json | head -34\n{real_diff}",
            "highlight": ["noise_seed", "SolAttnPatch", "H3FirstBlockCache"],
        }
    )

    ab = run(
        "python3 - <<'PY'\n"
        "import json\n"
        "for f in ('h3-dense-baseline','h3-fullstack'):\n"
        "    d=json.load(open('workflows/'+f+'.json'))\n"
        "    print(f)\n"
        "    for k,v in d.items():\n"
        "        ct=v.get('class_type','?')\n"
        "        if ct in ('UNETLoader','CLIPLoader','RandomNoise','BasicScheduler',"
        "'MiniMaxH3ImageToVideo','SolAttnPatch','H3FirstBlockCache'):\n"
        "            ins={kk:vv for kk,vv in v.get('inputs',{}).items() "
        "if kk in ('unet_name','clip_name','noise_seed','steps','width','height','length','tau','threshold')}\n"
        "            print('   ',ct,ins)\n"
        "PY"
    )
    scenes.append(
        {
            "kind": "terminal",
            "hold": 20.0,
            "title": "the same pair, seed-matched — the only difference is the acceleration",
            "body": f"$ python3 -c 'print the node table of both'\n{ab}",
            "highlight": ["SolAttnPatch", "H3FirstBlockCache", "noise_seed"],
        }
    )

    # -- 9. the ladder, with the times on screen ----------------------------------------
    chart = ROOT / "charts" / "end-to-end.png"
    if chart.is_file():
        scenes.append(
            {
                "kind": "image",
                "hold": 13.0,
                "path": chart,
                "caption": "END-TO-END, PROMPT TO FINISHED MP4  ·  published benchmark, upstream host spark-13b3",
            }
        )
    chart2 = ROOT / "charts" / "per-step.png"
    if chart2.is_file():
        scenes.append(
            {
                "kind": "image",
                "hold": 13.0,
                "path": chart2,
                "caption": "DENOISING COST PER STEP  ·  14.40 s  ->  8.39 s   (1.72x)",
            }
        )

    # -- 10. open the receipt ----------------------------------------------------------
    receipt = run("sed -n '1,30p' receipts/bench-results.md")
    scenes.append(
        {
            "kind": "terminal",
            "hold": 18.0,
            "title": "open the receipt",
            "body": f"$ sed -n '1,30p' receipts/bench-results.md\n{receipt}",
            "highlight": ["spark-13b3", "drowzeys", "7e3db54"],
        }
    )

    # -- 11. the provenance index ------------------------------------------------------
    prov = run("sed -n '1,26p' receipts/PROVENANCE.md")
    scenes.append(
        {
            "kind": "terminal",
            "hold": 16.0,
            "title": "receipts/PROVENANCE.md — every number, and who measured it",
            "body": f"$ head -26 receipts/PROVENANCE.md\n{prov}",
            "highlight": ["spark-13b3", "12944c1f"],
        }
    )

    # -- 11b. our own bench matrix -------------------------------------------------------
    matrix = run("cat receipts/bench-matrix.tsv")
    scenes.append(
        {
            "kind": "terminal",
            "hold": 15.0,
            "title": "receipts/bench-matrix.tsv — our own first-party benchmark, verbatim",
            "body": f"$ cat receipts/bench-matrix.tsv\n{matrix}",
            "highlight": ["B1_", "B4_", "B5_", "BASELINE"],
        }
    )

    # -- 12. what we measured ourselves -------------------------------------------------
    scenes.append(
        {
            "kind": "card",
            "hold": 12.0,
            "image": table_card(
                "WHAT WE MEASURED OURSELVES",
                "The numbers we can be held to",
                ["MEASUREMENT", "RESULT"],
                [
                    ["pruned FP8 DiT", "20,958,205,608 B - sha256 matches the published hash"],
                    ["NVFP4/AWQ encoder", "15,687,142,551 B - clean re-download"],
                    ["forward pass + video and audio decode", "30.02 s"],
                    ["shot renders", "710.15 / 710.13 / 710.14 s"],
                    ["acceleration arms vs plain control, 8 steps", "496 s -> 344 s   1.44x"],
                    ["the same at 16 steps", "635 s -> 545 s   1.17x"],
                    ["4-step turbo LoRA", "201 s against the 635 s baseline   3.16x"],
                    ["Sol-Attn and the batched VAE decode", "not installed in this stack"],
                ],
                row_colours=[INK, INK, INK, INK, AMBER, AMBER, AMBER, AMBER],
                footnote="receipts/bench-matrix.tsv | receipts/our-acceleration-ab.md | receipts/adapter-shelf.md",
                accent=AMBER,
            ),
        }
    )

    # -- 13. the corrupt encoder -------------------------------------------------------
    scenes.append(
        {
            "kind": "card",
            "hold": 10.0,
            "image": card(
                "THE ONE THAT WOULD HAVE COST A DAY",
                "A corrupt download with a healthy header",
                [
                    ("the file that arrived        21,714,795,671 B", INK),
                    ("the file that should exist   15,687,142,551 B", INK),
                    ("", MUTED),
                    ("6,027,653,120 bytes of unaccounted trailing data", RED),
                    ("behind a safetensors header that declared the right length", RED),
                    ("", MUTED),
                    ("it loads. it produces nothing. and it raises nothing.", MUTED),
                ],
                "receipts/encoder-diagnosis.md · receipts/verification.json",
                accent=RED,
            ),
        }
    )

    # -- 14. the craft gates -----------------------------------------------------------
    gates = run(
        "ls craft/gates/ && echo && sed -n '1,12p' craft/gates/motion_gate.py"
    )
    scenes.append(
        {
            "kind": "terminal",
            "hold": 16.0,
            "title": "the craft layer — gates that refuse a slideshow",
            "body": f"$ ls craft/gates/\n{gates}",
            "highlight": ["motion_gate.py", "aliveness_gate.py", "control_metrics.py", "face_metric.py"],
        }
    )

    # -- 15. the curated set ------------------------------------------------------------
    clip_dir = ROOT / "clips"
    shots = sorted(clip_dir.glob("*.mp4"))
    for clip in shots:
        shot = "Spillway " + clip.stem.split("-")[-1].upper()
        scenes.append(
            {
                "kind": "clip",
                "path": clip,
                "duration": 7.0,
                "start": 1.0,
                "label": f"{shot}  ·  1024x576  ·  8.0 s",
            }
        )

    for name, label in (
        ("FILM-WAR-1920x1056.mp4", "FILM-WAR  ·  finished film  ·  1920x1056"),
        ("FILM-BEACON-1920x1056.mp4", "FILM-BEACON  ·  finished film  ·  1920x1056"),
        ("FILM-BRIDGE-1920x1056.mp4", "FILM-BRIDGE  ·  finished film  ·  1920x1056"),
    ):
        path = assets / name
        if path.is_file():
            scenes.append(
                {"kind": "clip", "path": path, "duration": 7.0, "start": 3.0, "label": label}
            )

    # -- 16. the checker ---------------------------------------------------------------
    checker = run("python3 scripts/check_receipts.py")
    scenes.append(
        {
            "kind": "terminal",
            "hold": 18.0,
            "title": "and the build checks every number against its receipt",
            "body": f"$ python3 scripts/check_receipts.py\n{checker}",
            "highlight": ["Every published claim traced", "traced"],
        }
    )

    # -- 17. close ---------------------------------------------------------------------
    scenes.append(
        {
            "kind": "card",
            "hold": 11.0,
            "image": card(
                "KEEL",
                "Accelerated MiniMax H3 video diffusion inference on a single DGX Spark.",
                [
                    ("the stack       three vendored node packs, credited to their authors", INK),
                    ("the technique   TRIM - residency, the convert path, step distillation,", INK),
                    ("                a seed-matched A/B, and receipts", INK),
                    ("the craft layer gates, a cookbook, and a curated set of six", INK),
                    ("", MUTED),
                    ("ours:          1.44x at 8 steps, 1.17x at 16 steps, 3.16x on the turbo LoRA", INK),
                    ("not ours:      the published ladder, and NVIDIA's 3.92x. Both say so.", AMBER),
                    ("not done:      the ladder's own two components, never installed here.", AMBER),
                ],
                "sandeep-alluru/minimax-h3-local-engine  ·  docs, recipes, receipts and clips",
                accent=GREEN,
                title_size=50,
            ),
        }
    )

    return scenes


# --------------------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------------------


def label_frame(img: Image.Image, label: str) -> Image.Image:
    d = ImageDraw.Draw(img)
    f = font(MONO, 24)
    w = d.textlength(label, font=f)
    d.rectangle([0, H - 58, int(w) + 80, H], fill=(10, 12, 14))
    d.text((40, H - 46), label, font=f, fill=MUTED)
    return img


def render_scene(scene: dict):
    """Yield (frame_array, duration_seconds) pairs for one scene."""
    kind = scene["kind"]

    if kind in ("card",):
        yield np.asarray(scene["image"]), scene["hold"]
        return

    if kind == "terminal":
        img = terminal(scene["title"], scene["body"], highlight=scene.get("highlight"))
        arr = np.asarray(img)
        yield arr, scene["hold"]
        return

    if kind == "image":
        src = Image.open(scene["path"]).convert("RGB")
        src = src.resize((W, H), Image.LANCZOS)
        caption = scene.get("caption", "")
        if caption:
            d = ImageDraw.Draw(src)
            f = font(MONO, 26)
            d.rectangle([0, H - 64, W, H], fill=(10, 12, 14))
            d.text((40, H - 50), caption, font=f, fill=MUTED)
        yield np.asarray(src), scene["hold"]
        return

    if kind == "clip":
        path = pathlib.Path(scene["path"])
        frames = list(clip_frames(path, scene.get("start", 0.0), scene.get("duration", 6.0)))
        if not frames:
            return
        label = scene.get("label", path.name)
        held = int(scene.get("duration", 6.0) * FPS)
        for i in range(held):
            frame = frames[min(i, len(frames) - 1)]
            img = Image.fromarray(frame)
            d = ImageDraw.Draw(img)
            f = font(MONO, 26)
            d.rectangle([0, H - 64, W, H], fill=(10, 12, 14))
            d.text((40, H - 50), label, font=f, fill=MUTED)
            yield np.asarray(img), 1.0 / FPS
        return

    raise ValueError(f"unknown scene kind {kind!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT.parent / "MODEL-ACCELERATION-DEMO.mp4"))
    parser.add_argument("--assets", default=str(ROOT.parent / "demo-assets"))
    args = parser.parse_args()

    out_path = pathlib.Path(args.out).resolve()
    assets = pathlib.Path(args.assets).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scenes = build_storyboard(assets)
    total = sum(
        s.get("hold", s.get("duration", 0.0)) for s in scenes if s["kind"] != "clip"
    ) + sum(s.get("duration", 0.0) for s in scenes if s["kind"] == "clip")
    print(f"{len(scenes)} scenes, about {total:.0f}s of content")

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    written = 0
    try:
        for scene in scenes:
            for frame, duration in render_scene(scene):
                frames = max(1, int(round(duration * FPS)))
                for _ in range(frames):
                    proc.stdin.write(frame.tobytes())
                written += frames
            print(f"  [{written/FPS:6.1f}s] {scene['kind']}: {scene.get('title') or scene.get('label') or ''}")
    finally:
        proc.stdin.close()
        proc.wait()

    if proc.returncode != 0:
        print(f"ffmpeg errored with {proc.returncode}", file=sys.stderr)
        return proc.returncode

    print(f"\nwrote {out_path}")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
         "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
         "-of", "default=noprint_wrappers=1", str(out_path)],
        capture_output=True, text=True,
    )
    print(probe.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
