# Model Acceleration — MiniMax H3 on a single DGX Spark

**Model Acceleration** is the discipline: attention optimization, caching, quantization, and platform fixes — applied until a model's measured wall-clock falls. This repository is the discipline's record for **MiniMax H3**. A 5-second H3 clip (864×480, 124 frames, video + native stereo audio) renders in **312.7 s stock** on a single NVIDIA GB10. With this stack: **202.5 s — 1.54× end-to-end, 1.72× per denoising step (14.40 s → 8.39 s/step)**. Every number on this page traces to a receipt in [`receipts/`](receipts/).

H3 packs text, audio and video latents into one ~38K-row sequence with full self-attention, so attention is ~70% of the hot path. This repo is the acceleration stack we built around that shape — three installable ComfyUI node packages ported and packaged from NVIDIA's Sol-Engine approach for GB10/SM121, the checkpoint and adapter work that makes a 33B dense DiT resident on a single Spark, and the production discipline (locked stills, takes with receipts) that turns a fast demo into finished film.

## The result

Same prompt, same seed, GPU idle and ≤75 °C for every row. Full raw data: [`receipts/bench-results.md`](receipts/bench-results.md).

**End-to-end (prompt → finished mp4)**

| Config | Wall | vs dense |
|---|---:|---:|
| Dense (stock ComfyUI, no accelerations) | 312.7 s | 1.00× |
| FirstBlockCache only | 215.7 s | 1.45× |
| **Full stack** | **202.5 s** | **1.54×** |

**Denoising cost per step** (864×480, 124 frames, 20 steps)

| Config | s/step | vs dense |
|---|---:|---:|
| Dense | 14.40 | 1.00× |
| Sol-Attn (KingGore, tau 1.0, all steps sparse) | 10.88 | 1.32× |
| Sol-Attn INT8+TMA (kijai, tau 1.3, 6 dense steps) | 11.11 | 1.30× |
| FirstBlockCache only (thr 0.08) | 9.72 | 1.48× |
| Sol-Attn + FirstBlockCache | 8.09 | 1.78× |
| **Full stack (+ batched VAE decode)** | **8.39** | **1.72×** |

## The stack

| # | Technique | What it does | Measured (GB10) |
|---|---|---|---|
| 1 | **Sol-Attn sparse attention** | Routes each query block to only the top-scoring KV blocks (route density ~0.225); the rest is a pooled compensating term | 14.40 → 10.88 s/step (**1.32×**) |
| 2 | **INT8 QK + TMA variant** | Sage-style smoothed-K INT8 in the exact branch + TMA descriptors on Blackwell — kernel cosine vs dense SDPA 0.99995 | quality headroom at equal speed (11.11 s/step) |
| 3 | **FirstBlockCache** | Runs block 0 every step; if its residual barely moved, skips the other 49 blocks and re-applies the cached tail — skips 6 of 20 steps under its guards | 14.40 → 9.72 s/step (**1.48×**) |
| 4 | **Batched VAE tile decode** | Batches same-shape spatial tiles through the 36-layer ViT decoder instead of one launch at a time | 4.871 → 2.933 s/chunk (**1.66×**) |
| 5 | **AdaLN precompute** | ~13B of H3's 33B parameters live in AdaLN branches; their modulation outputs are precomputed into the pruned checkpoint | free at runtime |
| 6 | **Pruned FP8-scaled checkpoints** | FL2VA and Ref2VA DiTs cut from 35.7 GB BF16 → **21.0 GB FP8-scaled** each — the memory work that makes the model resident on one Spark | −41% checkpoint size |
| 7 | **NVFP4/AWQ text encoder** | Qwen3-VL-32B encoder in NVFP4/AWQ mixed storage instead of full precision | fits alongside the DiT in unified memory |
| 8 | **GB10 spin-wait patch** | One-line vLLM fix (`busy_loop_s 1 → 0.002`) stopping the server from burning CPU cores that share the GB10 SoC thermal budget | [`custom_nodes/H3-SolAttn-SM121/GB10_SPIN_WAIT_PATCH.md`](custom_nodes/H3-SolAttn-SM121/GB10_SPIN_WAIT_PATCH.md) |

Field note, recorded in the receipts: `torch.flex_attention` on sm_121 compiles, runs — and is numerically wrong (cosine 0.9167–0.9688 vs SDPA). Do not use it on this architecture.

## Node packages

Installable ComfyUI custom nodes, each with its own README, benchmarks and tests:

- [`custom_nodes/H3-SolAttn-SM121/`](custom_nodes/H3-SolAttn-SM121/) — sparse attention + INT8/TMA variant, the agent-executable [`RECIPE.md`](RECIPE.md), workflows, patches
- [`custom_nodes/H3-FirstBlockCache/`](custom_nodes/H3-FirstBlockCache/) — the cache node with benchmark suite and comparison-grid tooling
- [`custom_nodes/H3-Motion-Context/`](custom_nodes/H3-Motion-Context/) — motion-context/control nodes with example workflows

## The adapter shelf — turbo step-distillation LoRAs

Deployed in the stack. Binaries are **not** in git (1.96 GB each); SHA-256 pinned here so any copy can be verified.

| Adapter | Bytes | SHA-256 | Buys |
|---|---:|---|---|
| `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16` | 1,956,192,992 | `c396a9a06f58399e9df9754b18299818d84a2ddd371724ba48fe4a41221437dc` | FL2V generation in **4 steps** instead of 20 |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16` | 1,956,193,000 | `2339acdf19bfe123f46b971ea35d367a84adb85de43627e1eceafa5b2b111e` | the 8-step middle rung |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16` | 1,956,193,000 | `5b9ab5ade15d0775676d01a907268a69a1468dc6033b3b0d3ded5502f3ebb84c` | Ref2V in 4 steps |

Training-side proof (a full 500-step LoRA run executed on the Spark, plus the persona LoRA programme): [`training/TRAINING.md`](training/TRAINING.md).

## Best clips — the curated set

Six clips survive curation (Oct 25, 2026) — only the best are kept and shipped here. Everything else the stack produced was a test, a benchmark, or a receipt: their data stays in [`receipts/`](receipts/), but they are not showcase clips. The **v0.1.0 (draft) release is the single download point for all six**; the three keeper shots are also in git under [`clips/`](clips/).

| Clip | Measured facts | Get it |
|---|---|---|
| **FILM-WAR** | Finished film — 30 s, 1080p, produced with this stack | Release asset |
| **FILM-BEACON** | Finished film — 30 s, 1080p, produced with this stack | Release asset |
| **FILM-BRIDGE** | Finished film — 30 s, 1080p, produced with this stack | Release asset |
| ***Spillway* S01 keeper** (take-005) | 1024×576, 192 frames, 8 s, 20 steps, rendered end-to-end in **710.15 s** from a hash-locked photographic still; signed receipt (settings, input hashes, clip SHA-256 `98c964bf…`); owner-verdicted keeper ("looks good") | [`clips/spillway-s01-keeper.mp4`](clips/spillway-s01-keeper.mp4) + release asset |
| ***Spillway* S02 keeper** (take-002) | 1024×576, 192 frames, 8 s, 20 steps, **710.13 s**; clip SHA-256 `2e836122…`; verdict KEEPER in the lane's selection record after a source-grounded re-review | [`clips/spillway-s02-keeper.mp4`](clips/spillway-s02-keeper.mp4) + release asset |
| ***Spillway* S03 keeper** (take-002) | 1024×576, 192 frames, 8 s, 20 steps, **710.14 s**; clip SHA-256 `ca41bef4…`; the fire-crossing shot — selected after three rendered alternatives, its join with S02 verified by the lane | [`clips/spillway-s03-keeper.mp4`](clips/spillway-s03-keeper.mp4) + release asset |

The three *Spillway* clips are keeper shots from a production run — **not a finished film**: the production was halted by the owner on Oct 25, 2026 with 3 of its 15 shots locked as keepers. Full clip index with sizes and hashes: [`clips/INDEX.md`](clips/INDEX.md).

## The craft layer

Speed is half the story; the other half is control. [`craft/`](craft/) holds the prompt cookbook (`PROMPT-COOKBOOK.md`) and the quality gates used in production — motion, aliveness, face and control metrics (`craft/gates/`). [`production/`](production/) holds the pinned production harness (`tools/pinned-h3/`), the exact model-stack config (`H3-WORKFLOW-CONFIG.json` — file names + hashes), and the locked-stills manifest (15 stills, hash-manifested before any video was generated).

## Reproduce it

1. [`RECIPE.md`](RECIPE.md) — the agent-executable setup: every number above was measured on the machine it describes.
2. [`docs/deployment-guide.md`](docs/deployment-guide.md) — hardware paths, from a 3090 pair to H100 quads, and the serve recipes.
3. Weights are gated and stay off git: MiniMax H3 from [MiniMaxAI/MiniMax-H3](https://huggingface.co/MiniMaxAI/MiniMax-H3); the workflow config names the exact files and hashes this stack runs.

## Receipts

| Receipt | File |
|---|---|
| Raw speed ladder (dense vs each technique vs full stack, machine spec, hygiene notes) | [`receipts/bench-results.md`](receipts/bench-results.md) |
| Model-file verification — SHA-256 + tensor dtype counts for all four model files | [`receipts/verification.json`](receipts/verification.json) |
| Real forward-pass proof — 124 frames 512×288, video+audio decode, 30.02 s, output SHA-256 `dac049a4…` | [`receipts/forward-receipt.json`](receipts/forward-receipt.json) |
| Corrupt-encoder diagnosis and the SHA-pinned replacement | [`receipts/encoder-diagnosis.md`](receipts/encoder-diagnosis.md) |
| The acceleration A/B that did **not** ship (SageAttention patch rejected by the installed build — tested, recorded, baseline kept) | [`receipts/sage-attention-ab.md`](receipts/sage-attention-ab.md) |
| Keeper take-005 receipt (710.15 s, verdict KEEPER) | [`receipts/keeper-receipt.json`](receipts/keeper-receipt.json) |
| Best-clips curation note (what was removed from git, and where the sources live) | [`receipts/CURATION-NOTE.md`](receipts/CURATION-NOTE.md) |

## Layout

```text
README.md                  this page
RECIPE.md                  agent-executable speed recipe
custom_nodes/              the three node packages
craft/                     prompt cookbook + quality gates
production/                pinned harness, workflow config, stills manifest
receipts/                  every number's evidence
training/                  LoRA configs + run notes
clips/                     the curated best clips only (index: clips/INDEX.md)
docs/                      deployment field guide
```

## What is not here

Model weights and checkpoints (the 199 GB weights tree, the 35.7 GB BF16 / 21.0 GB FP8 DiTs), the turbo-LoRA binaries (hashes pinned above instead), credentials of any kind, and persona datasets/imagery. The finished 1080p films ship as Release assets, not git blobs.
