# Model Acceleration — MiniMax H3 on a single NVIDIA DGX Spark

**MiniMax H3 on one 128 GB DGX Spark, with the ComfyUI node stack, the production harness, the
craft gates, and the receipts to prove every number on this page.**

This repository is the public face of a piece of work that started as a link and turned into a
production. It holds:

* the **acceleration stack** for MiniMax H3 on GB10 (`sm_121`) — three installable ComfyUI node
  packs, one recipe, two workflows (dense baseline and full stack) so you can A/B them yourself;
* the **measurements**, separated into what this team ran and what was published by someone else,
  with the attribution attached to every row;
* a **craft layer** — gates that refuse a slideshow and call it a video, a prompt cookbook, and a
  pinned production harness;
* and **six curated clips** from a real production, hashed and indexed.

---

## Results

### The published speed ladder

Measured by the author of the community Sol-Engine port for a single DGX Spark, on their host
`spark-13b3`, and published in their repository. Reproduced here verbatim, with attribution.

**End-to-end — prompt to finished mp4.** 864×480, 124 frames (5.17 s @ 24 fps), 20 steps, same
prompt and seed 46 across the ladder.

| Config | Wall | vs dense |
|---|---:|---:|
| Dense (stock ComfyUI, no accelerations) | 312.7 s | 1.00× |
| FirstBlockCache only | 215.7 s | 1.45× |
| **Full stack (kijai Sol-Attn + FirstBlockCache + batched VAE decode)** | **202.5 s** | **1.54×** |

**Denoising cost per step.**

| Config | s/step | vs dense |
|---|---:|---:|
| Dense | 14.40 | 1.00× |
| Sol-Attn only (kijai, tau 1.3, INT8+TMA, 6 dense steps) | 11.11 | 1.30× |
| Sol-Attn only (KingGore, tau 1.0, all steps sparse) | 10.88 | 1.32× |
| FirstBlockCache only (threshold 0.08) | 9.72 | 1.48× |
| kijai Sol-Attn + FirstBlockCache | 8.09 | 1.78× |
| **Full stack (+ batched VAE decode)** | **8.39** | **1.72×** |

**Batched VAE tile decode**, one temporal chunk at 864×480, warm: 4.871 s sequential → **2.933 s
batched (1.66×)**. Output is `allclose`, not bit-identical — batch size changes fp16 kernel
selection. Max abs diff 1.56e-2, mean 5.29e-4 on a [-1,1] pixel range.

![end-to-end ladder](charts/end-to-end.png)
![per-step ladder](charts/per-step.png)

> **Where these numbers come from.** They are **not** measurements this team took. They are the
> published benchmark of `drowzeys/keys-SM121-Optimized-MiniMax-H3-Nvidia-Sol-Engine-Kijai-SolAttn_Triton-Single-DGX-Spark`
> at commit `7e3db54`, reproduced byte-for-byte in `receipts/bench-results.md`. This team did not
> re-run this ladder on our own hardware. See **What we measured ourselves** below for the
> first-party numbers, and `receipts/PROVENANCE.md` for the number-by-number map.
>
> For reference, NVIDIA's own published GB10 figure for the same model is **710.6 s → 181.3 s
> (3.92×)** at 480p / 5 s / 50 steps, on a pruned FP8 DiT with an FP8 Qwen3-VL conditioner —
> `NVlabs/Sana` @ `sol-engine`, `models/minimax_h3/README.md`.

### What we measured ourselves

First-party numbers, on our own DGX Spark, each with its own receipt.

| Measurement | Result | Receipt |
|---|---|---|
| Pruned FP8 FL2VA DiT, the checkpoint we actually run | 20,958,205,608 B (21.0 GB), SHA-256 `12944c1f…` | `receipts/verification.json` |
| NVFP4/AWQ Qwen3-VL-32B encoder, re-downloaded clean | 15,687,142,551 B (15.7 GB) | `receipts/verification.json` |
| The same encoder, first download | 21,714,795,671 B — 6,027,653,120 unaccounted trailing bytes | `receipts/encoder-diagnosis.md` |
| A real H3 forward pass **and** video+audio decode, 512×288, 124 frames, 2 steps | **30.02 s** | `receipts/forward-receipt.json` |
| Sage + FirstBlockCache combined vs baseline | 39.8 → 34.1 s/step — **1.17×** | `receipts/our-acceleration-ab.md` |
| The same two isolated | 347 s → 344 s — **~1.0×** | `receipts/our-acceleration-ab.md` |
| Spillway keeper, Sage arm | rejected before sampling, 35.507 s/step baseline | `receipts/sage-attention-ab.md` |
| Spillway keeper render, 1024×576, 192 frames, 20 steps | 710.15 s (S01) · 710.13 s (S02) · 710.14 s (S03) | `receipts/spillway-keepers.md` |
| Checkpoint sizes, every published variant, byte-exact | 66.3 GB BF16 · 34.0 GB INT8 ConvRot · 21.0 GB pruned FP8 | `receipts/checkpoint-sizes.md` |

### The honest gap

Three things this repository will not pretend:

1. **We did not reproduce the ladder above.** When this team A/B'd the stack on its own box it
   measured **1.17×** from Sage + FirstBlockCache combined and **~1.0×** when the two were
   isolated, with FirstBlockCache alone at roughly zero, and the batched VAE node was never
   enabled at all. The Sol-Attn stack was left *unproven here, not disproven* — but it was not
   proven either. The published ladder remains a published benchmark.
2. **The three Spillway keepers were rendered with `"accelerate": false`.** They are evidence for
   the harness and the gates, not for the speed.
3. **Our own speed claim is the negative one.** The one first-party performance experiment that
   completed found no measurable gain from the attention backend it tested. That result is in the
   repository in full.

### The memory problem this stack actually solves

On a 128 GB Spark, precision is not a preference — it is residency. The pruned FP8 DiT plus the
NVFP4/AWQ encoder plus both VAEs is **42.4 GB**, comfortably inside the 121 GB the runtime sees.
The BF16 DiT alone is 66.3 GB, and the BF16 encoder is 51.5 GB; together with the VAEs that is
123.6 GB before a single activation is allocated.

| DiT | Encoder | + VAEs | Total | Fits 121 GB? |
|---|---|---|---:|---|
| BF16 66.3 GB | BF16 51.5 GB | 5.81 GB | 123.6 GB | No |
| BF16 66.3 GB | NVFP4 15.7 GB | 5.81 GB | 87.8 GB | Yes |
| INT8 ConvRot 34.0 GB | NVFP4 15.7 GB | 5.81 GB | 55.5 GB | Yes |
| **Pruned FP8 21.0 GB** | **NVFP4 15.7 GB** | 5.81 GB | **42.4 GB** | **Yes — the production pair** |

This is also why NVIDIA's own GB10 recipe uses a pruned FP8 DiT and an FP8 Qwen3-VL. Byte-exact
sizes and the reasoning are in `receipts/checkpoint-sizes.md`.

---

## Where this came from

Told plainly, because the interesting part is not the numbers — it is the order things happened
in.

**It started with a link and a question.** On 2026-10-20 the owner sent the team NVIDIA's
Sol-Engine branch for MiniMax H3 and asked them to work out how it was able to do what it was
doing. A minute later came an X post: a video of MiniMax H3 animating typography, with the
question *"check this video how did they do it with minimaxh3."* The Sol-Engine branch was the
answer to that question, and it became the project.

**Then we found the thing that actually fits.** NVIDIA's Sol-Engine ships per-GPU runtimes for
GB10, GB200, H100, A100, RTX 4090 and RTX 5090 — SGLang-side, with its own model directories.
What a ComfyUI user needs is different: a single Spark, node packs you can install, and a
workflow you can open. On 2026-10-21 we found the community port that does exactly that, plus
two standalone ComfyUI node packs that cover the same ground from different directions. All
three are vendored here under `custom_nodes/`, each credited, each left as its authors shipped
it.

**Then we did the part that was left.** NVIDIA's recipe and the community port both stop at
"here is the fast configuration". This repository is the part after that:

* the **precision work** — working out which checkpoints actually fit in unified memory, and
  catching a text encoder that arrived corrupt (6 GB of trailing garbage behind a healthy
  header) before it cost us a render;
* the **platform work** — the GB10 spin-wait fix, the Blackwell `sm_121` attention paths, and the
  decision that `torch flex_attention` is numerically wrong on this architecture and must not be
  used;
* the **production harness** — a pinned toolset, a stills manifest, and a shot list;
* the **craft layer** — motion, aliveness, control and face gates that refuse a slideshow and
  call it a video, plus the prompt cookbook that came out of them;
* and the **receipts** — every number above, filed where you can check it.

**And then the production stopped.** The owner halted the film lane on 2026-10-25. The three
Spillway keepers in `clips/` are what survived that halt, and they are in this repository as
keepers — not as a finished film, and not as a speed demonstration.

---

## What this actually does for you

1. **Puts MiniMax H3 on one Spark at production resolution.** The node packs, the two VAEs, the
   pruned FP8 DiT and the NVFP4 encoder: a 21.0 GB model with a 15.7 GB text encoder, both in
   unified memory, with no multi-GPU and no second machine.
2. **Gives you two workflows so the comparison is yours, not ours.**
   `workflows/h3-dense-baseline.json` is stock ComfyUI. `workflows/h3-fullstack.json` is the full
   stack. Same seed, same prompt, same box — the only variable is the acceleration.
3. **Tells you which parts to distrust.** The Sol-Attn kernel numerics table, the
   FirstBlockCache step curve, the `flex_attention` failure, the corrupt encoder, the Sage
   A/B. These are the things that cost real days if you meet them cold.
4. **Keeps the craft bar.** The gates in `craft/gates/` are what stopped a 32 %-alive clip being
   published as a film. A shot has to move, and the gate has to say so in numbers.
5. **Lets you check every claim.** `python3 scripts/check_receipts.py` re-hashes the curated set
   and refuses to let the front page say anything that no receipt backs.

## What it does not do

* It does not reproduce the published ladder. That ladder was measured upstream, on a host that
  is not ours, and this repository says so wherever it appears.
* It does not claim the acceleration stack made our clips. The keepers were rendered with
  acceleration off.
* It does not ship model weights. It ships the recipes and the receipts.
* It does not resume the halted production. Only the owner can do that.
* It does not settle the licence question. That one is the owner's, and it is deferred.

---

## Install

**1 — Node packs.** Copy the three directories into your ComfyUI `custom_nodes/`:

```bash
cd /path/to/ComfyUI/custom_nodes
cp -r /path/to/minimax-h3-local-engine/custom_nodes/H3-SolAttn-SM121   .
cp -r /path/to/minimax-h3-local-engine/custom_nodes/H3-FirstBlockCache .
cp -r /path/to/minimax-h3-local-engine/custom_nodes/H3-Motion-Context .
```

`H3-SolAttn-SM121` is the full port (Sol-Attn + FirstBlockCache + batched VAE + the GB10
spin-wait patch). It ships its own installer if you would rather point it at your ComfyUI:

```bash
bash custom_nodes/H3-SolAttn-SM121/install.sh --comfy-dir /path/to/ComfyUI
```

**2 — Weights.** Into `ComfyUI/models/`:

| Target | File | Bytes |
|---|---|---:|
| `diffusion_models/` | `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 20,958,205,608 |
| `diffusion_models/` | `minimax_h3_ref2va_pruned_fp8_scaled.safetensors` | 20,958,205,608 |
| `text_encoders/` | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15,687,142,551 |
| `vae/` | `minimax_h3_video_vae_fp16.safetensors` | 5,207,808,496 |
| `vae/` | `minimax_h3_audio_vae_fp32.safetensors` | 605,254,808 |

**3 — Workflow.** Open `workflows/h3-fullstack.json` for the accelerated path and
`workflows/h3-dense-baseline.json` for the control. Same prompt, same seed, same resolution — the
only difference is the acceleration nodes. See `workflows/README.md`.

**4 — Check your claim.** From the repository root:

```bash
python3 scripts/check_receipts.py
```

`RECIPE.md` is the same thing written for an agent instead of a person.

---

## What's in the stack, and who wrote each part

| Part | What it does | Origin |
|---|---|---|
| **Sol-Attn** (KingGore) | Top-K KV-block routing with an exact-prefix sink, Triton. Cosine 0.99998 against dense SDPA. | NVIDIA's kernel design; `KingGore/ComfyUI_sol-attn_Blackwell`, vendored pre-patched for `sm_121` |
| **Sol-Attn** (kijai) | INT8/TMA variant, tau 1.3, 6 dense steps. Cosine 0.99995. | NVIDIA's kernel design; `kijai/ComfyUI-SolAttn_triton` |
| **FirstBlockCache** | Runs block 0, reuses the cached tail when the per-row diff ratio is flat. Threshold 0.08. | NVIDIA's `GB10/cache_line.py`; ComfyUI pack by `duckyshell` |
| **Batched VAE decode** | Batches same-shape tiles through the 36-layer ViT decoder. 1.66× on decode. | NVIDIA's `GB10/vae_shard.py`; ComfyUI node by the port author |
| **Motion-Context** | Clips that genuinely continue across a join — motion and audio carry over. | `NikoDemon80/ComfyUI-H3-Motion-Context` |
| **GB10 spin-wait patch** | `busy_loop_s` 1 → 0.002. Upstream reports CPU 333 % → 89 % and SoC −11 °C. | Port author's patch, for NVIDIA's GB10 vLLM spin-wait |
| **Pruned FP8 + NVFP4 checkpoints** | The only DiT/encoder pair that fits one Spark. | Published by the model repository; we verified our download against the published hash |
| **Craft gates** | Motion, aliveness, control and face gates. | Ours |
| **Production harness** | Pinned tools, stills manifest, shot list, keeper receipts. | Ours |
| **Receipts** | Every published number, mapped to who measured it. | Ours |

---

## Four things that will cost you a day if you don't know them

**1 — `torch flex_attention` is wrong on Blackwell.** It compiles, it runs, and it does not error.
Cosine similarity against dense SDPA is **0.9167 at S=1536** and **0.9688 at S=4096**. The error
compounds across 50 blocks × 20 steps into visible noise. The working alternatives measure
0.99995–0.99998. Do not reach for `flex_attention` on `sm_121`.

**2 — the text encoder can arrive corrupt and still look healthy.** The safetensors header
declared the right length; the payload behind it was 6,027,653,120 bytes of garbage. It shows up
as an encoder that loads and then produces nothing useful. Check
`complete_offset_boundary` and the trailing byte count before you trust a download — that is what
`receipts/encoder-diagnosis.md` is for.

**3 — FirstBlockCache's step curve is U-shaped, not monotone.** The per-row diff ratio falls from
.179 at step 1 to a minimum around step 10 and climbs back to .249 by step 19. With the guards
(`start_step=3`, `end_dense_steps=2`, `max_consecutive_skips=2`) it skips 6 of 20 steps — 6, 7, 9,
10, 12, 13 — but the tail is where it gets expensive again. Set the guard from the curve, not from
a gut feel.

**4 — two Sparks over Ethernet is slower than one Spark.** Context parallelism across two nodes
runs at 5.52 GB/s over fabric against 503 GB/s over NVLink. Splitting the render across two
machines loses far more than the parallelism wins. This is why the whole stack here is designed
to run on one box.

---

## The curated set

Six clips. Three finished films and three Spillway keeper shots. Hashes, geometry and the exact
status of each one are in `clips/INDEX.md`; `scripts/check_receipts.py` re-hashes them on every
run and fails if the set changes.

| | Clip | What it is |
|---|---|---|
| 1 | `spillway-s01-keeper.mp4` | Spillway S01 take 5 — **owner-locked keeper**, 710.15 s |
| 2 | `spillway-s02-keeper.mp4` | Spillway S02 take 2 — **owner-locked keeper** after a source-grounded re-review, 710.13 s |
| 3 | `spillway-s03-keeper.mp4` | Spillway S03 take 2 — **pre-halt agent selection, not owner-locked**, 710.14 s |
| 4 | `FILM-WAR-30s-1080p.mp4` | Finished film, 1920×1056, 31.104 s |
| 5 | `FILM-BEACON-30s-1080p.mp4` | Finished film, 1920×1056, 31.104 s |
| 6 | `FILM-BRIDGE-30s-1080p.mp4` | Finished film, 1920×1056, 31.104 s |

---

## Requirements

* NVIDIA DGX Spark (GB10, `sm_121`), or any Blackwell-class board with ≥ 64 GB unified memory
* ComfyUI on `aarch64`, CUDA 13, torch 2.11+
* The `pinned-h3` production toolset under `production/tools/pinned-h3/` (Python 3.11, `opencv-python`,
  `numpy`)
* For the craft gates: `opencv-python` and `numpy`

## Repo layout

```
minimax-h3-local-engine/
├── README.md                       this page
├── RECIPE.md                       the same thing written for an agent
├── LAUNCH-PACKET.md                internal: state, gaps, checklist, owner decisions
├── charts/                         the ladder, and the script that draws it
├── clips/                          the curated set — six clips, indexed and hashed
│   ├── INDEX.md
│   ├── spillway-s01-keeper.mp4
│   ├── spillway-s02-keeper.mp4
│   └── spillway-s03-keeper.mp4
├── craft/                          the craft layer
│   ├── PROMPT-COOKBOOK.md
│   └── gates/                      motion, aliveness, control, face
├── custom_nodes/                   three ComfyUI node packs, each credited
│   ├── H3-SolAttn-SM121/           Sol-Attn + FBC + batched VAE + spin-wait patch + workflows
│   ├── H3-FirstBlockCache/         standalone FirstBlockCache pack
│   └── H3-Motion-Context/          clip chaining across joins
├── docs/                           deployment guide
├── production/                     pinned harness, workflow config, stills manifest
├── receipts/                       every number, and where it came from
│   ├── PROVENANCE.md               number-by-number map — start here
│   ├── bench-results.md            the published ladder, verbatim, attributed
│   ├── checkpoint-sizes.md         byte-exact size table and the residency math
│   ├── spillway-keepers.md         the three keepers, their lock status, the halt
│   ├── verification.json           model-file hashes and tensor dtype counts
│   ├── forward-receipt.json        a real forward pass and decode
│   ├── keeper-receipt.json         the S01 keeper, with motion metrics
│   ├── sage-attention-ab.md        the A/B that found no gain
│   ├── encoder-diagnosis.md        the corrupt encoder, and the fix
│   └── CURATION-NOTE.md            why the set is six
├── scripts/
│   └── check_receipts.py           fails the build if a claim stops matching its receipt
└── training/                       turbo LoRA shelf and its training config
```

## Credits

**NVIDIA Sol-Engine** — the original. `NVlabs/Sana` branch `sol-engine`, including the per-GPU
MiniMax H3 runtimes, the GB10 recipe, and the Sol-Attention design.
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

**xmarre** — the ComfyUI H3 Sol integration this stack is measured against.
<https://github.com/xmarre/ComfyUI-Sol-H3>

**Comfy-Org** — the H3 checkpoints, including the pruned FP8 DiT and the NVFP4/AWQ encoder.
<https://huggingface.co/Comfy-Org/MiniMax-H3>

**MiniMax** — H3 itself.
<https://huggingface.co/MiniMaxAI/MiniMax-H3>
