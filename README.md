<p align="center">
  <img src="assets/keel-logo.svg" width="420" alt="Keel" />
</p>

<p align="center"><b>Accelerated video diffusion interface on a single DGX Spark.</b></p>

<p align="center">For people who run video diffusion on one 128 GB box: installable ComfyUI node packs, a weight set that fits in unified memory, and a receipt behind every number — with MiniMax H3 as the first model it runs.</p>

<p align="center">
  <a href="docs/deployment-guide.md">Docs</a> ·
  <a href="#install">Install</a> ·
  <a href="#benchmarks">Benchmarks</a> ·
  <a href="#watch">Watch</a>
</p>

<p align="center">
  <video src="assets/keel-teaser.mp4" poster="assets/hero-poster.png" width="880" muted loop playsinline controls preload="metadata"></video>
</p>

<p align="center">
  <a href="assets/keel-teaser.mp4"><b>▶ Watch the teaser</b></a> ·
  <a href="#watch">Every clip →</a>
</p>

<a id="benchmarks"></a>

**MiniMax H3 end-to-end — prompt to finished video.** Every row below is either **published**,
measured by the repository named in the last column, or **measured here**, with the file that
holds it. The two are never blended, and the geometries are not the same, so read the columns and
not just the speedup.

| Engine | Hardware | Geometry | Steps | Seconds | Speedup | Source |
|---|---|---|---:|---|---:|---|
| Stock MiniMax H3 — no acceleration | DGX Spark, GB10 | 832×480, 124f | 50 | 710.6 s | 1.00× | published · NVlabs/Sana `sol-engine` |
| **NVlabs Sana Sol-Engine** — full opt | DGX Spark, GB10 | 832×480, 124f | 50 | **181.3 s** | **3.92×** | published · NVlabs/Sana `sol-engine` |
| Stock ComfyUI — no acceleration | DGX Spark, `spark-13b3` | 864×480, 124f | 20 | 312.7 s | 1.00× | published · community SM121 port |
| **Community Sol-Engine port** — full stack | DGX Spark, `spark-13b3` | 864×480, 124f | 20 | **202.5 s** | **1.54×** | published · community SM121 port |
| ComfyUI-Sol-H3 — SOL on, default | RTX PRO 6000, SM120 | not stated | not stated | 420.81 → **400.94 s** | 1.05× | published · xmarre/ComfyUI-Sol-H3 |
| ComfyUI-Sol-H3 — SOL on, speed mode | RTX PRO 6000, SM120 | not stated | not stated | 420.81 → **380.57 s** | 1.11× | published · xmarre/ComfyUI-Sol-H3 |
| **Keel** — acceleration vs plain control | DGX Spark, GB10 | 1280×704, 124f | 8 | 496 → **344 s** | **1.44×** | **measured here** · `receipts/bench-matrix.tsv` |
| **Keel** — acceleration vs plain control | DGX Spark, GB10 | 1280×704, 124f | 16 | 635 → **545 s** | **1.17×** | **measured here** · `receipts/bench-matrix.tsv` |
| **Keel** — 4-step turbo LoRA | DGX Spark, GB10 | 1280×704, 124f | 4 | **201 s** | **3.16×** | **measured here** · `receipts/bench-matrix.tsv` |

<sub>**Conditions.** Rows 1–2: MiniMax H3, 832×480, 124 frames, 50 steps, one DGX Spark (GB10),
as published by NVlabs/Sana on branch `sol-engine`; that release states no seed or batch size.
Rows 3–4: MiniMax H3, 864×480, 124 frames, 20 steps, seed 46, one DGX Spark on host
`spark-13b3`, measured by the author of the community SM121 port. Rows 5–6: MiniMax H3 on an
NVIDIA RTX PRO 6000 Blackwell (SM120), torch 2.10.0+cu130; that release states no resolution, no
frame count and no seed, so those cells are left blank rather than guessed. Rows 7–9: MiniMax H3,
1280×704, 124 frames, one DGX Spark, seed matched between the control and the treatment,
`accelerate: false` in the control. Every row is end-to-end, model load to written video, and
every row is a single render — no batching.</sub>

![end-to-end wall clock, plain control against the accelerated arm](charts/keel-ab.png)

<sub>Measured here, `receipts/bench-matrix.tsv`. The plain control and the accelerated arm share
the seed, the geometry, the step count and the scheduler, and differ only in the acceleration.</sub>

Every ladder behind these rows — the published end-to-end and per-step arms, NVIDIA's published
figures, the ComfyUI-Sol-H3 A/B, and the byte-exact residency ladder — is in
[`docs/benchmarks.md`](docs/benchmarks.md), each with the conditions that produced it.

---

## What Keel is

**Keel is** an interface for accelerated video diffusion on one 128 GB DGX Spark. MiniMax H3 — a 33B
joint video-and-audio diffusion model — is the first model it runs. It ships three installable
ComfyUI node packs, the weight set that actually fits in unified memory, a seed-matched A/B method
so you can measure the difference on your own box, and a checker that stops the build if a
published number stops matching its receipt.

Keel is the ComfyUI side of the same problem NVIDIA's Sol-Engine solves. Sol-Engine is their
inference codebase with their own kernels, and `Sol-Attn` is their name for their method. Keel is
an independent implementation on the ComfyUI side — the node packs, the resident-weight recipe,
the step-distillation adapters, and the discipline around the numbers. The published speed ladder
quoted above belongs to the community Sol-Engine port, and it is attributed wherever it appears.

The largest first-party speedup below comes from the 4-step turbo LoRA: a step-count reduction as
much as an acceleration. The Sol-Attn kernel and the batched VAE decode are installed in this
stack and active in the shipped workflow, and running the published 1.54× ladder here — with both
of them in — is the next run.

---

## 📰 News

- **2026-10-25 — `v0.1.0`** — First release.
  - Three installable ComfyUI node packs: the SM121 Sol-Attn port, a standalone FirstBlockCache
    pack, and Motion-Context clip chaining.
  - The resident weight set — pruned FP8 DiT plus NVFP4/AWQ encoder — at **42.46 GB** for the
    denoiser, the encoder and both decoders.
  - A verified number table: the published ladder, the published NVIDIA and ComfyUI-Sol-H3
    figures, and our own seed-matched A/B at **1.44×** (8 steps), **1.17×** (16 steps) and
    **3.16×** (4-step turbo LoRA).
  - Six rendered clips and a demo video, with hashes for all of them.
  - **Verified on a fresh clone.** A clean clone installs the node packs against a clean ComfyUI
    and renders the shipped `workflows/h3-fullstack.json` end to end — 864×480, 124 frames, seed
    46 — with FirstBlockCache skipping the same six sampling steps as the published ladder, and
    the output byte-identical across three runs. Receipt:
    [`receipts/fresh-clone-render.md`](receipts/fresh-clone-render.md).
  - `scripts/check_receipts.py`, run on every push and every pull request, which stops the build
    when a published number stops matching the file behind it.

---

## Install

This is the MiniMax H3 model coverage — the first model the interface runs. The node packs, the
resident-weight recipe and the measurement method are the model's, so a second model is a weight
set and a workflow away from the same stack.

**Requirements**

* NVIDIA DGX Spark (GB10, `sm_121`), or any Blackwell-class board with ≥ 64 GB unified memory
* ComfyUI on `aarch64`, CUDA 13, torch 2.11+
* The `pinned-h3` production toolset under `production/tools/pinned-h3/` (Python 3.11,
  `opencv-python`, `numpy`)
* For the craft gates: `opencv-python` and `numpy`

**1 — Node packs.** Copy the three directories into your ComfyUI `custom_nodes/`:

```bash
cd /path/to/ComfyUI/custom_nodes
cp -r /path/to/keel/custom_nodes/H3-SolAttn-SM121   .
cp -r /path/to/keel/custom_nodes/H3-FirstBlockCache .
cp -r /path/to/keel/custom_nodes/H3-Motion-Context .
```

`H3-SolAttn-SM121` is the full port — Sol-Attn, FirstBlockCache, the batched VAE decode and the
GB10 spin-wait patch — and it ships its own installer if you would rather point it at your
ComfyUI:

```bash
bash custom_nodes/H3-SolAttn-SM121/install.sh --comfy-dir /path/to/ComfyUI
```

The batched VAE decode is an import-time patch on `MiniMaxH3VideoVAE.tiled_decode`, not a graph
node, so it is **on** by default and disabled with `H3_VAE_BATCHED=0`. With it off, a "full
stack" number is not a full stack number.

After you restart ComfyUI, the pack registers itself:

```
Import times for custom nodes:
  h3_fbc_node.py       |  0.42 s
  h3_vae_batch.py      |  0.11 s
  sol_attn_node.py     |  0.38 s
```

**Already have the packs installed?** Run the installer again — it skips files that are already
in place and leaves your ComfyUI alone.

**2 — Weights.** Into `ComfyUI/models/`. Every file, with its size and published SHA-256, is in
[`receipts/weights.md`](receipts/weights.md). The pair that fits one Spark:

| Target | File | Bytes |
|---|---|---:|
| `diffusion_models/` | `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 20,958,205,608 |
| `diffusion_models/` | `minimax_h3_ref2va_pruned_fp8_scaled.safetensors` | 20,958,205,608 |
| `text_encoders/` | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15,687,142,551 |
| `vae/` | `minimax_h3_video_vae_fp16.safetensors` | 5,207,808,496 |
| `vae/` | `minimax_h3_audio_vae_fp32.safetensors` | 605,254,808 |

**3 — Workflow.** Open `workflows/h3-fullstack.json` for the accelerated path and
`workflows/h3-dense-baseline.json` for the control. Same prompt, same seed, same resolution — the
only difference is the acceleration nodes. See [`workflows/README.md`](workflows/README.md).

**4 — Check your claim.** From the repository root:

```bash
python3 scripts/check_receipts.py
```

[`RECIPE.md`](RECIPE.md) is the same thing written as a procedure, and
[`docs/deployment-guide.md`](docs/deployment-guide.md) is the longer version.

---

## The technique: Trim

**Trim** is Keel's named technique. NVIDIA's is Sol-Attn; Trim is the set of choices that make one
machine enough, plus the method of proving they work.

Trim means three things, in order: **fit the model to the machine, cut the steps, then measure the
cut.**

| | What it does | Weights it touches | Measured effect |
|---|---|---|---|
| **Trim-Residency** | Picks the weight set that fits in the 121 GB a Spark actually shows the runtime: a pruned FP8 DiT and an NVFP4/AWQ encoder instead of the BF16 pair. | `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` (20.96 GB), `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (15.69 GB) | **42.46 GB** for DiT + encoder + both VAEs, against 123.60 GB for the BF16 pair — the difference between running and not running. The precision cost is nil: NVIDIA measure their FP8 baseline at 13,428 ms/step against the BF16 model's 13,417 ms, a **0.08 % difference**. *(FP8 cost: published · NVIDIA. Residency: measured here.)* |
| **Trim-INT8** | The convert path for machines with more room: INT8 ConvRot DiTs at 34.04 GB, or the pruned INT8 ConvRot DiTs at 20.97 GB, in place of the BF16 66.28 GB. | `minimax_h3_fl2va_int8_convrot.safetensors` (34.04 GB), `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (20.97 GB) | **A residency choice.** Its effect is residency, measured in the models table below: 55.54 GB with the NVFP4 conditioner. The speed measurements in this table come from the other five rows. |
| **Trim-NVFP4** | The INT4 conditioner, and the download discipline that goes with it: quote a checkpoint size from the safetensors header, never from `stat`. | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (15.69 GB) | Caught a **21,714,795,671-byte** encoder with **6,027,653,120 bytes** of trailing garbage behind a healthy header, and a **truncated BF16 DiT** 30.6 GB short of its own header. *(Measured here — `receipts/encoder-diagnosis.md`.)* |
| **Trim-Step** | Step distillation. A 4-step or 8-step turbo LoRA replaces 20 sampling steps. | `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` (1.96 GB) and siblings | **201 s** for a 4-step 1280×704 render against the 635 s 16-step plain baseline — **3.16×**. A step-count reduction as much as an acceleration, and a quality trade rather than a free win. *(Measured here.)* |
| **Trim-A/B** | The measurement method: a control and a treatment that differ *only* in the acceleration, on the same seed, the same geometry, the same step count, the same scheduler. | none | **1.44×** at 8 steps, **1.17×** at 16 steps, against matched plain controls. *(Measured here — `receipts/bench-matrix.tsv`.)* |
| **Trim-Receipts** | The discipline: every published number maps to who measured it, and a checker fails the build when a number loses its receipt. | none | **The trust mechanism**, and the reason the other five rows can be believed. *(Measured here — `scripts/check_receipts.py`.)* |

### What this actually does for you

You keep one machine. You download one weight set that fits in unified memory, instead of
discovering halfway through a render that it never will. You cut twenty sampling steps to four
when you want a draft and you keep twenty when you want the quality. And when you quote a number
— to yourself or to anyone else — you can point at the file that holds it.

### What's next

* **Run the published 1.54× ladder on this stack**, with the Sol-Attn kernel and the batched VAE
  decode active, and file the receipt beside theirs.
* **Separate Sage attention from FirstBlockCache** inside the accelerated arms, so each technique
  in the table carries its own number rather than sharing one.
* **Give Trim-INT8 its own timing**, so all six techniques have a measured effect.

---

## Watch

Nine pieces of real output, all rendered with this stack. Three finished films and three Spillway
shots, plus the demo video.

### Finished films

| | Film | Geometry | Length |
|---|---|---|---|
| ![Beacon — a woman carrying a lit pot through a burning street](assets/posters/film-beacon.png) | [Beacon](https://github.com/sandeep-alluru/minimax-h3-local-engine/releases/download/v0.1.0/FILM-BEACON-1920x1056.mp4) | 1920×1056, 24 fps | 31.104 s |
| ![War — a soldier behind a ruined wall](assets/posters/film-war.png) | [War](https://github.com/sandeep-alluru/minimax-h3-local-engine/releases/download/v0.1.0/FILM-WAR-1920x1056.mp4) | 1920×1056, 24 fps | 31.104 s |
| ![Bridge — a rifle against a broken bridge](assets/posters/film-bridge.png) | [Bridge](https://github.com/sandeep-alluru/minimax-h3-local-engine/releases/download/v0.1.0/FILM-BRIDGE-1920x1056.mp4) | 1920×1056, 24 fps | 31.104 s |

### Spillway shots

| | Shot | Geometry | Length |
|---|---|---|---|
| ![Spillway S01](assets/posters/shot-s01.png) | [S01](https://github.com/sandeep-alluru/minimax-h3-local-engine/releases/download/v0.1.0/spillway-s01.mp4) | 1024×576, 24 fps | 8.0 s |
| ![Spillway S02](assets/posters/shot-s02.png) | [S02](https://github.com/sandeep-alluru/minimax-h3-local-engine/releases/download/v0.1.0/spillway-s02.mp4) | 1024×576, 24 fps | 8.0 s |
| ![Spillway S03](assets/posters/shot-s03.png) | [S03](https://github.com/sandeep-alluru/minimax-h3-local-engine/releases/download/v0.1.0/spillway-s03.mp4) | 1024×576, 24 fps | 8.0 s |

### Demo

[▶ The full demo video](https://github.com/sandeep-alluru/minimax-h3-local-engine/releases/download/v0.1.0/keel-demo.mp4)
— the acceleration story end to end, from real captures. Rebuilt from the repository by
`scripts/make_demo.py`.

Every file above is hashed. Geometry, wall time and digest for each one are in
[`clips/INDEX.md`](clips/INDEX.md), and the checker re-hashes them on every run.

---

## Models & weights

**Keel ships no weights. Not one byte.** Every checkpoint is published by somebody else and
downloaded by us. The complete inventory — every DiT variant, the text encoder, both decoders and
the turbo LoRAs, with source, byte-exact size, published SHA-256 and what was done to each one —
is in [`receipts/weights.md`](receipts/weights.md).

| Model family | Files | Source | What it is |
|---|---|---|---|
| **DiT** — the denoiser | `minimax_h3_{fl2va,ref2va}_*.safetensors` | `Comfy-Org/MiniMax-H3` | Two variants of the same 33B transformer: **FL2VA** (first and last frame to video and audio) and **Ref2VA** (reference image, video or audio to video and audio) |
| **Text encoder** | `qwen3vl_32b_minimax_h3_*.safetensors` | `Comfy-Org/MiniMax-H3` | Qwen3-VL-32B, conditioning the prompt |
| **Decoders** | `minimax_h3_video_vae_fp16`, `minimax_h3_audio_vae_fp32` | `Comfy-Org/MiniMax-H3` | Video decoder and audio decoder — H3 is joint video **and** native stereo audio |
| **Turbo LoRAs** | `minimax_h3_{fl2v,ref2v}_turbo_*.safetensors` | `Comfy-Org/MiniMax-H3` | Step-distillation adapters that cut 20 sampling steps to 4 or 8 |

The set that fits one Spark, with the bytes that decide it:

| DiT | Encoder | + decoders | Total | Fits 121 GB? |
|---|---|---:|---:|---|
| BF16 66.28 GB | BF16 51.51 GB | 5.81 GB | 123.60 GB | No |
| BF16 66.28 GB | NVFP4 15.69 GB | 5.81 GB | 87.78 GB | Yes |
| INT8 ConvRot 34.04 GB | NVFP4 15.69 GB | 5.81 GB | 55.54 GB | Yes |
| **Pruned FP8 20.96 GB** | **NVFP4 15.69 GB** | 5.81 GB | **42.46 GB** | **Yes — the production pair** |

The five files that make up that pair, and the step-distillation adapter:

| File | Source | Bytes | SHA-256 | What we did to it |
|---|---|---:|---|---|
| `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | `Comfy-Org/MiniMax-H3` | 20,958,205,608 | `12944c1f7791637e7de12208aef04da82bd26b95271b1b47d817364315ade993` | untouched — the denoiser this stack runs |
| `minimax_h3_ref2va_pruned_fp8_scaled.safetensors` | `Comfy-Org/MiniMax-H3` | 20,958,205,608 | `f86f2f79ebd2d76eb8eeb46091e83982e6ff51d255747e7b16e92834b392b8e9` | untouched — the Ref2VA arm |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `Comfy-Org/MiniMax-H3` | 15,687,142,551 | `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6` | untouched, re-downloaded — the conditioner this stack runs |
| `minimax_h3_video_vae_fp16.safetensors` | `Comfy-Org/MiniMax-H3` | 5,207,808,496 | `7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522` | untouched — the video decoder |
| `minimax_h3_audio_vae_fp32.safetensors` | `Comfy-Org/MiniMax-H3` | 605,254,808 | `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48` | untouched — the audio decoder |
| `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` | `Comfy-Org/MiniMax-H3` | 1,956,192,992 | `c396a9a06f58399e9df9754b18299818d84a2ddd371724ba48fe4a41221437dc` | untouched — the step-distillation adapter |

"Pruned", "FP8-scaled" and "INT8 ConvRot" are the publisher's names for their conversions, not
ours. Byte-exact sizes for every other variant, and the residency arithmetic, are in
[`receipts/checkpoint-sizes.md`](receipts/checkpoint-sizes.md) and
[`receipts/weights.md`](receipts/weights.md).

The pruned FP8-scaled build brings each denoiser to **21.0 GB** and the NVFP4/AWQ conditioner to
**15.7 GB** — **42.46 GB** for a denoiser, a conditioner and both decoders, which is what actually
fits in a Spark's 121 GB of visible unified memory.

---

## How the numbers are verified

A number without a file behind it is a rumour. Every figure in this repository comes from one of
two places, and the distinction is kept visible everywhere:

* **Published** — measured by somebody else, quoted from the repository that measured it, with the
  host and the revision recorded. The community SM121 ladder is quoted byte-for-byte from commit
  `7e3db54`; NVIDIA's figures and ComfyUI-Sol-H3's figures are quoted from their own releases.
* **Measured here** — taken on a DGX Spark and filed in `receipts/` with the host, the
  configuration, the wall time and, where there is a file, its SHA-256.

The index is [`receipts/PROVENANCE.md`](receipts/PROVENANCE.md): one row per number, with where
it came from. The full set of tables, each with its conditions and its chart, is
[`docs/benchmarks.md`](docs/benchmarks.md).

And the checker enforces it:

```bash
python3 scripts/check_receipts.py
```

It fails when a number on the front page has no file behind it, when a clip's hash drifts, when a
seventh clip appears in the set, or when the README grows a licence heading. It is stdlib-only,
touches no network and no GPU, and it runs on every push and every pull request through
[`.github/workflows/claims.yml`](.github/workflows/claims.yml).

### The method

One GPU, idle, seed matched. The plain control and the accelerated arm share the seed, the
geometry, the step count, the scheduler and the sampler, and differ only in the acceleration. A
contended run is not a slower run, it is a different experiment. The full matrix, including the
rows that are not comparable, is in [`receipts/bench-matrix.tsv`](receipts/bench-matrix.tsv), and
[`RECIPE.md`](RECIPE.md) is the procedure to run from a fresh box.

Two things worth knowing before you quote any of it. `torch flex_attention` is wrong on Blackwell
— cosine similarity against dense SDPA is 0.9167 at S=1536 and 0.9688 at S=4096, and the error
compounds across 50 blocks and 20 steps into visible noise. And a download can be broken and still
look right: quote a checkpoint size from the safetensors header, never from `stat`. Both cases,
with the numbers, are in [`docs/performance-notes.md`](docs/performance-notes.md).

---

## Credits

**NVIDIA Sol-Engine** — the original. `NVlabs/Sana` branch `sol-engine`, including the per-GPU
MiniMax H3 runtimes, the GB10 recipe and the Sol-Attention design.
<https://github.com/NVlabs/Sana/tree/sol-engine>

**drowzeys** — the community port for a single DGX Spark, and the published benchmark this
repository reproduces with attribution.
<https://github.com/drowzeys/keys-SM121-Optimized-MiniMax-H3-Nvidia-Sol-Engine-Kijai-SolAttn_Triton-Single-DGX-Spark>

**KingGore** — the Blackwell ComfyUI Sol-Attn pack, vendored pre-patched for `sm_121`.
<https://github.com/KingGore/ComfyUI_sol-attn_Blackwell>

**kijai** — the Triton Sol-Attn variant and the ComfyUI node base.
<https://github.com/kijai/ComfyUI-SolAttn_triton>

**duckyshell** — the standalone FirstBlockCache ComfyUI pack.
<https://github.com/duckyshell/ComfyUI-MiniMaxH3-FirstBlockCache>

**NikoDemon80** — Motion-Context, clip chaining that survives a join.
<https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context>

**xmarre** — ComfyUI-Sol-H3, the ComfyUI-native Sol integration, and the matched A/B discipline
this method was written in the light of.
<https://github.com/xmarre/ComfyUI-Sol-H3>

**Comfy-Org** — the H3 checkpoints, including the pruned FP8 DiT and the NVFP4/AWQ encoder.
<https://huggingface.co/Comfy-Org/MiniMax-H3>

**MiniMax** — H3 itself.
<https://huggingface.co/MiniMaxAI/MiniMax-H3>

The three node packs under `custom_nodes/` are third-party works redistributed exactly as their
authors published them, under their own licences. Their upstream files are unmodified.

Their respective upstream licences and attribution notices apply.

---

## Citation

```bibtex
@misc{keel,
  title        = {Keel: accelerated video diffusion interface on a single DGX Spark},
  howpublished = {\url{https://github.com/sandeep-alluru/minimax-h3-local-engine}},
  note         = {ComfyUI node packs, resident weight set, and receipt-backed measurements.
                 MiniMax H3 is the first model it runs.}
}
```
