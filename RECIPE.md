# RECIPE — Model Acceleration, MiniMax H3 on a single DGX Spark

**Who this is for:** an agent (or a person) that has to get from "nothing installed" to "I have a
measured stock-vs-accelerated comparison and a receipt for each number", without guessing.

**What you are *not* doing here:** re-creating the upstream benchmark as your own work. The
published ladder in `receipts/bench-results.md` was measured by the community port's author on
host `spark-13b3`. If you re-run it, you are producing a *first-party* measurement, and it should
be filed as one — under your own host name, in your own receipt, next to theirs.

Every command below is idempotent and safe to re-run. Nothing here starts a production, publishes
anything, or touches the halted Spillway lane.

---

## 0 — Before you touch a GPU

```bash
nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv
```

You need a **GB10 (`sm_121`, compute capability 12.1)** to reproduce the numbers in this repo, and
you need **≥ 64 GB unified memory**. On a discrete GPU with 24 GB of VRAM this stack does not fit
and none of the timings below are comparable.

Check the machine is idle before you time anything:

```bash
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```

An empty table is the precondition for a timing run. A contended run is not a slower run, it is a
different experiment — the upstream bench excludes contended runs and says so.

## 1 — Install the node packs

```bash
git clone <this-repo> minimax-h3-local-engine
cd minimax-h3-local-engine

COMFY=/path/to/ComfyUI
for pack in H3-SolAttn-SM121 H3-FirstBlockCache H3-Motion-Context; do
  cp -r "custom_nodes/$pack" "$COMFY/custom_nodes/"
done
```

`H3-SolAttn-SM121` carries the Sol-Attn patcher, the FirstBlockCache node, the batched-VAE
monkeypatch, the GB10 spin-wait patch and the upstream installer:

```bash
bash custom_nodes/H3-SolAttn-SM121/install.sh --comfy-dir "$COMFY"
```

The batched VAE decode is a monkeypatch applied on import, not a graph node. It is **on** by
default and is disabled with `H3_VAE_BATCHED=0`. That matters: with it off, your "full stack"
number is not the full stack.

Verify the pack actually landed:

```bash
ls "$COMFY/custom_nodes/ComfyUI_sol-attn_Blackwell/sol_attn_node.py" \
   "$COMFY/custom_nodes/h3_fbc_node.py" \
   "$COMFY/custom_nodes/h3_vae_batch.py"
```

## 2 — Install the weights, and check them

```bash
mkdir -p "$COMFY/models/diffusion_models" "$COMFY/models/text_encoders" "$COMFY/models/vae"
```

| File | Target | Bytes | SHA-256 |
|---|---|---:|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | `diffusion_models/` | 34,038,892,334 | `7ad4c73e6e378b822ffd1629f27f632d3787d95f5e468e3af958f98c58df96a5` |
| `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | `diffusion_models/` | 20,958,205,608 | `12944c1f7791637e7de12208aef04da82bd26b95271b1b47d817364315ade993` |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `text_encoders/` | 15,687,142,551 | `61f55b01f03e9cd9ec2b10e3084e74519230373135aef5c84ec6b7ec04208340` |
| `minimax_h3_video_vae_fp16.safetensors` | `vae/` | 5,207,808,496 | `7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522` |
| `minimax_h3_audio_vae_fp32.safetensors` | `vae/` | 605,254,808 | `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48` |

**Check the encoder before you trust it.** A truncated or corrupted safetensors file can have a
healthy header and garbage behind it. The failure mode is a model that loads and then produces
nothing. The receipt `receipts/encoder-diagnosis.md` documents the exact case we hit: the file
arrived at 21,714,795,671 bytes — 6,027,653,120 bytes of unaccounted trailing data past a header
that declared the right length.

```bash
python3 - <<'PY'
import json, pathlib, hashlib
for p in sorted(pathlib.Path("receipts").glob("*.json")):
    data = json.loads(p.read_text())
    for w in data.get("weights", []) or []:
        print(f'{w["file"]:60s} {w["bytes"]:>16,}  trailing={w.get("unaccounted_trailing_bytes")}  '
              f'complete={w.get("complete_offset_boundary")}')
PY
```

A file is good when `complete_offset_boundary` is `true` and `unaccounted_trailing_bytes` is `0`.

**Which checkpoint to use.** The upstream ladder was measured with the **pruned INT8 ConvRot** DiT
(34.0 GB). Production on one Spark uses the **pruned FP8-scaled** DiT (21.0 GB) — the FP8 pair is
what leaves room for the encoder and the VAEs in unified memory. See
`receipts/checkpoint-sizes.md` for the full table and the residency arithmetic.

## 3 — Run the A/B

Both workflows live in `workflows/`. They are identical except for the acceleration nodes, the
output prefix, and nothing else: **same prompt, same seed (46), same resolution (864×480), same
length (124 frames), same 20 steps, same scheduler and sampler.**

| | File | Acceleration nodes |
|---|---|---|
| Control | `workflows/h3-dense-baseline.json` | none |
| Treatment | `workflows/h3-fullstack.json` | `SolAttnPatch` (tau 1.3, INT8 QK) → `H3FirstBlockCache` (threshold 0.08) |

Start ComfyUI and queue the control first, wait for it to finish, then queue the treatment:

```bash
cd "$COMFY" && python3 main.py --listen 0.0.0.0 --port 8188
```

```bash
# queue the control
curl -sS -X POST http://127.0.0.1:8188/prompt \
  -H 'Content-Type: application/json' \
  -d "{\"prompt\": $(python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))' workflows/h3-dense-baseline.json))}"
```

Time it from the ComfyUI execution log, not from wall-clock around the `curl` — the prompt
submission is not the render:

* `prompt` → `execution_cached`/`executed` for node `92 SaveVideo` is the end-to-end number;
* the sampler rows are the per-step number.

### What a valid run looks like

* GPU idle before the run, `nvidia-smi --query-compute-apps` empty.
* GPU ≤ 75 °C, SM clock ≥ 2398 MHz during sampling.
* The treatment run must show the batched VAE active — if the log does not mention batched tile
  decode, `H3_VAE_BATCHED=0` is set somewhere and the number is not the full-stack number.
* Same seed in both runs. If you changed the seed, the comparison is void.

### Expected shape

The upstream ladder on `spark-13b3` landed at 312.7 s dense and 202.5 s full stack. **Your
numbers will not match those exactly** — different host, different driver, different seeds for
the noise. What you are looking for is the *shape*: the full stack meaningfully below dense, and
the per-step ratio roughly 1.7×.

If you get **less** than the upstream ladder, that is a legitimate first-party result and it
belongs in this repository. It does not belong in the same table as the upstream numbers.

## 4 — File your receipt

A measurement without a receipt is a rumour. Write one:

```json
{
  "scope": "first-party re-measurement of the published ladder",
  "host": "<your-host-name>",
  "gpu": "NVIDIA GB10, sm_121",
  "workflow": "workflows/h3-fullstack.json",
  "seed": 46,
  "settings": { "width": 864, "height": 480, "frames": 124, "steps": 20,
                "sampler": "res_multistep", "scheduler": "simple" },
  "dense_seconds": 0.0,
  "fullstack_seconds": 0.0,
  "end_to_end_ratio": 0.0,
  "seconds_per_step_dense": 0.0,
  "seconds_per_step_fullstack": 0.0,
  "per_step_ratio": 0.0,
  "artifacts": [{ "path": "...", "sha256": "...", "bytes": 0 }],
  "notes": "what was different from the upstream run"
}
```

Then add the row to `receipts/PROVENANCE.md` and, if it is a new number on the front page, to
`receipts/` as well. Run the checker:

```bash
python3 scripts/check_receipts.py
```

It fails if a published number has no receipt behind it, if a clip's hash has drifted, or if the
curated set has grown a seventh member.

## 5 — Run the craft gates on what you made

A render that completes is not a shot. The gates are what stop a slideshow being published as a
film.

```bash
pip install opencv-python numpy        # gate dependencies
python3 craft/gates/motion_gate.py  <your.mp4> [<your.mp4> ...]
python3 craft/gates/aliveness_gate.py <your.mp4> [<your.mp4> ...]
```

`motion_gate.py` refuses a clip whose mean frame difference is below the band. Thresholds are
calibrated against this team's own clips: a visibly moving control sits at mean 3.13–3.65, p95
7.45–15.76; known static failures sit at mean 0.07–0.89, p95 0.21–2.20. Exit code 1 means the
clip failed.

`aliveness_gate.py` answers the other question — is there enough going on to call it alive.

## 6 — Check the claims before you repeat them

```bash
python3 scripts/check_receipts.py
```

This is the same command CI runs. If it passes, every number on the front page of this repository
has a file behind it.

---

## What this recipe does not do

* It does not resume the halted Spillway production. Only the owner can.
* It does not publish, upload, or push anything anywhere.
* It does not touch the licence question. That is deferred by the owner.
* It does not claim the upstream ladder as this team's measurement. If you re-run it, the receipt
  is yours and the number stays yours.
