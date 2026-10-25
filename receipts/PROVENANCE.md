# PROVENANCE — who measured what, and where the receipt is

This is the index that `scripts/check_receipts.py` enforces. Every number that appears on the
front page of this repository has to appear in this file, and every file this file points at has
to exist.

There are three kinds of number in this repo, and they are never mixed:

| Kind | Meaning | Marked as |
|---|---|---|
| **PUBLISHED** | Measured by somebody else and reproduced here as their published result. | Named source, named host, link to the source file. |
| **OURS** | Measured by us, on our own hardware, and filed here. | Our receipt, our host, our hashes. |
| **CORRECTED** | Was in an earlier revision of this repo without support. | What it said, what the record actually says, what replaced it. |

---

## 1. The speed ladder — PUBLISHED (not ours)

Reproduced verbatim from `drowzeys/keys-SM121-Optimized-MiniMax-H3-Nvidia-Sol-Engine-Kijai-SolAttn_Triton-Single-DGX-Spark`
at commit `7e3db54a0ecf7fa524ee3b01ea9ef7092b0e3318`, file `bench/results.md`.
Upstream host `spark-13b3`. **We did not re-run this ladder.**

| Number | What it is | Receipt |
|---|---|---|
| `312.7 s` | Dense (stock ComfyUI), end-to-end, 864×480×124f, 20 steps | `receipts/bench-results.md` |
| `202.5 s` | Full stack (kijai Sol-Attn + FBC + batched VAE), end-to-end | `receipts/bench-results.md` |
| `1.54×` | End-to-end ratio, full stack vs dense | `receipts/bench-results.md` |
| `215.7 s` | FirstBlockCache only, end-to-end | `receipts/bench-results.md` |
| `1.45×` | End-to-end ratio, FBC only vs dense | `receipts/bench-results.md` |
| `14.40` | Dense, s/step | `receipts/bench-results.md` |
| `10.88` / `1.32×` | Sol-Attn only, KingGore (tau 1.0, all steps sparse), s/step | `receipts/bench-results.md` |
| `11.11` / `1.30×` | Sol-Attn only, kijai (tau 1.3, INT8+TMA, 6 dense steps), s/step | `receipts/bench-results.md` |
| `9.72` / `1.48×` | FirstBlockCache only (thr 0.08), s/step | `receipts/bench-results.md` |
| `8.09` / `1.78×` | kijai Sol-Attn + FBC, s/step | `receipts/bench-results.md` |
| `8.39` / `1.72×` | Full stack, s/step | `receipts/bench-results.md` |
| `4.871 s` → `2.933 s` / `1.66×` | Batched VAE tile decode, one temporal chunk at 864×480, warm | `receipts/bench-results.md` |
| `0.99998` / `0.99995` | Cosine similarity vs dense SDPA, Sol-Attn kernels (KingGore Triton, kijai bf16/TMA/INT8) | `receipts/bench-results.md` |
| `0.9167` @ S=1536, `0.9688` @ S=4096 | Cosine similarity of torch `flex_attention` on `sm_121` — **broken, do not use** | `receipts/bench-results.md` |
| `.179 … .067 … .249` | FirstBlockCache per-row diff ratio over 20 steps, threshold 0.08 — U-shaped, skips 6 of 20 steps | `receipts/bench-results.md` |
| `83.1 s/step`, `31 m 34 s`, `10–13 GB` free | 362-frame (15.1 s) clip, full stack minus batched VAE | `receipts/bench-results.md` |
| `20.77` s/step, `476.5 s` | Sol-Attn under contention — excluded from every comparison | `receipts/bench-results.md` |
| `5.52 GB/s` vs `503 GB/s` | Ethernet fabric vs NVLink — why CP=2 across two Sparks is slower | `drowzeys` README, quoted in the Oct-21 session record |
| `0.225` | Route density quoted from NVIDIA's own measurements | `drowzeys` `RECIPE.md` |

### NVIDIA's and xmarre's published numbers — PUBLISHED (not ours)

Full detail, with the quoted sentences, in `receipts/published-comparisons.md`.

| Number | What it is | Receipt |
|---|---|---|
| `710.6 s` → `181.3 s`, `3.92×` | NVIDIA Sol-Engine on DGX Spark, 832×480, 124 frames, 50 steps | `receipts/published-comparisons.md` |
| `13,428` ms/step vs `13,417` ms/step, `0.08%` | NVIDIA's FP8 baseline against the BF16 model's step cost — FP8 as residency, not as an optimisation | `receipts/published-comparisons.md` |
| `27.21` → `6.88` s, `3.95×` | NVIDIA Sol-Engine on 8× GB200, 768p@5s | `receipts/published-comparisons.md` |
| `420.81` → `400.94` s, `1.05×` | xmarre ComfyUI-Sol-H3, SOL on at the default `dense_evaluations=1`, RTX PRO 6000 SM120 | `receipts/published-comparisons.md` |
| `420.81` → `380.57` s, `1.11×` | xmarre, SOL on in the `dense_evaluations=0` speed mode, same host | `receipts/published-comparisons.md` |
| `374.84` → `332.56` s | the same xmarre pair, sampler wall only | `receipts/published-comparisons.md` |
| `312.57` → `298.69` s | xmarre Exact Runtime A/B, 17.18 GB peak VRAM either way | `receipts/published-comparisons.md` |

### NVIDIA's own published GB10 numbers — PUBLISHED (not ours)

| Number | What it is | Receipt |
|---|---|---|
| `710.6 s` → `181.3 s`, `3.92×` | NVIDIA Sol-Engine on DGX Spark, 480p@5s, 50 steps, pruned FP8 DiT + FP8 Qwen3-VL | `NVlabs/Sana` @ `sol-engine`, `models/minimax_h3/README.md` |
| `3.95×` vs Diffusers, `2.80×` vs SGLang, `8×` GB200 | Enze Xie (@xieenze_jr), Sol-Engine Day-1 MiniMax H3 announcement, 2026-08-03 | NVIDIA SANA announcement thread |
| `3.92×` / `4.27×` | DiT-forward speedup vs end-to-end speedup | NVIDIA's own config notes, `config/minimax_h3/gb10_fullopt.toml` |

---

## 2. Our own measurements — OURS

Measured by us on our own DGX Spark (`sm_121`). Hashes and byte counts are in the receipts.

| Number | What it is | Receipt |
|---|---|---|
| `20,958,205,608` bytes (`21.0 GB`) | Pruned FP8-scaled FL2VA DiT, SHA-256 `12944c1f7791637e7de12208aef04da82bd26b95271b1b47d817364315ade993` | `receipts/verification.json` |
| `20,970,379,616` bytes (`21.0 GB`) | Pruned INT8 ConvRot FL2VA DiT — the denoiser the shipped workflow names — SHA-256 `e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a`, re-hashed at render time | `receipts/weights.md`, `receipts/fresh-clone-render.md` |
| `5d4ac708…` | SHA-256 of the clip rendered by the shipped workflow from a fresh clone, 864×480, 124 frames — byte-identical across two runs | `receipts/fresh-clone-render.md` |
| steps **6, 7, 9, 10, 12, 13** skipped of 20 | FirstBlockCache's decisions on this stack — the same six the published ladder skips | `receipts/fresh-clone-render.md` |
| `15,687,142,551` bytes (`15.7 GB`) | NVFP4/AWQ Qwen3-VL-32B text encoder, re-downloaded clean | `receipts/verification.json` |
| `21,714,795,671` bytes | The corrupt encoder file: `6,027,653,120` unaccounted trailing bytes | `receipts/verification.json`, `receipts/encoder-diagnosis.md` |
| `5,207,808,496` / `605,254,808` bytes | Video VAE fp16 / audio VAE fp32, both complete, zero trailing bytes | `receipts/verification.json` |
| `30.02 s` | A real H3 forward pass **and** video+audio decode, 512×288, 124 frames, 2 steps | `receipts/forward-receipt.json` |
| `496 s` → `344 s`, **1.44×** | Acceleration arms vs plain control, 8 steps, 1280×704 | `receipts/bench-matrix.tsv` |
| `635 s` → `545 s`, **1.17×** | Acceleration arms vs plain control, 16 steps, 1280×704 (39.8 → 34.1 s/step) | `receipts/bench-matrix.tsv`, `receipts/our-acceleration-ab.md` |
| `201 s`, **3.16×** | 4-step turbo LoRA vs the 16-step plain baseline, 1280×704 | `receipts/bench-matrix.tsv`, `receipts/adapter-shelf.md` |
| `1,956,192,992` / `1,956,193,000` | Turbo LoRA sizes, SHA-256 verified on the weights tree | `receipts/adapter-shelf.md` |
| `35.507 s/step` | Spillway shot, 710.142 s over 20 steps — an actual-time signal, not a kernel timing | `receipts/sage-attention-ab.md` |
| `710.1506812029984 s` | Spillway **S01** shot, take 5 — 1024×576, 192 frames, 20 steps | `receipts/shot-receipt.json` |
| `710.13236 s` / `710.14137 s` | Spillway **S02** shot (take 2) / **S03** shot (take 2) | `receipts/spillway-shots.md` |
| `4.372` motion mean, `8.809` p95, `0.863` structure | Motion metrics on the S01 shot | `receipts/shot-receipt.json` |
| `98c964bf…`, `2e836122…`, `ca41bef4…` | SHA-256 of the three Spillway shots in `clips/` | `clips/INDEX.md`, verified by `scripts/check_receipts.py` |
| `1920×1056`, `744` frames, `31.104 s`, `24 fps` | Measured geometry and duration of the three finished films | `clips/INDEX.md` |

### Checkpoint sizes — OURS (published by the model repo, verified against our own download)

Full table with every variant, byte-exact, in `receipts/checkpoint-sizes.md`.

| Number | What it is |
|---|---|
| `66,280,487,368` bytes (`66.3 GB`) | BF16 FL2VA **and** Ref2VA DiT |
| `34,038,892,334` bytes (`34.0 GB`) | INT8 ConvRot FL2VA DiT (`34,038,894,550` for Ref2VA) |
| `20,958,205,608` bytes (`21.0 GB`) | Pruned FP8-scaled FL2VA **and** Ref2VA DiT |
| `20,970,379,616` bytes (`21.0 GB`) | Pruned INT8 ConvRot FL2VA **and** Ref2VA DiT |
| `51,506,295,256` bytes (`51.5 GB`) | BF16 Qwen3-VL-32B text encoder |
| `27,141,342,152` bytes (`27.1 GB`) | INT8 ConvRot Qwen3-VL-32B text encoder |
| `15,687,142,551` bytes (`15.7 GB`) | NVFP4/AWQ Qwen3-VL-32B text encoder |

---

## 3. Corrections — CORRECTED

What this repository said before, and what the record actually supports.

| Was | Record says | Now |
|---|---|---|
| `35.7 GB` BF16 DiT → `21.0 GB` FP8 | The BF16 FL2VA and Ref2VA DiTs are **66,280,487,368 bytes (66.3 GB)**. The nearest real figure is the INT8 ConvRot checkpoint at `34.0 GB`. `35.7 GB` matches no published checkpoint — **it is the size of a truncated download** that sat on disk under the right name, with a header declaring 66.3 GB. | `66.3 GB` BF16 → `21.0 GB` pruned FP8, and `34.0 GB` INT8 ConvRot → `21.0 GB` pruned INT8 ConvRot. Both byte-exact in `receipts/checkpoint-sizes.md`, which now also carries the truncation and the header check that catches it. |
| "3 of 15 shots locked" | The production stop record locks **two** shots (S01 take 5, S02 take 2). S03 take 2 is an **auto-selected shot** and is explicitly *not* signed off. | "Two locked shots carrying an explicit sign-off and one selected shot", spelled out per clip in `clips/INDEX.md` and `receipts/spillway-shots.md`. |
| Films described as "30 s, 1080p" | Measured: **1920×1056**, 744 frames, **31.104 s** at 24 fps, H.264 + 32 kHz stereo AAC. | Measured geometry in `clips/INDEX.md`. The release asset filenames keep the production lead's working names; the mismatch is flagged here. |
| Bench receipt on host `gb10-spark` | The ladder was measured upstream on host `spark-13b3`. | Host restored, provenance header added, upstream credited. |
| "Every row below was taken … on `gb10-spark`" | Upstream's own text says `spark-13b3`. | Replaced with an explicit provenance block. |
| Node packages described as "ported and packaged by us" | Each `custom_nodes/` tree is an upstream repository under its own licence. Two are byte for byte as published; the SM121 Sol-Attn pack carries our changes in three of its own files, and its vendored kijai/KingGore tree carries the pack author's four (see Credits in the README). | Credits section names each author, links each source, and states our changes file by file. The comparison against each upstream is in `receipts/vendored-trees.md`. |
| "The BF16 checkpoint is 35.7 GB … it fits" | 66.3 GB BF16 shares no 121 GB unified pool with a 51.5 GB BF16 encoder and the VAEs. | The FP8/NVFP4 row is the one that fits, and the guide says which. |
| Spillway shots presented as accelerated output | Every shot receipt records `"accelerate": false`. | Stated plainly wherever the shots appear. |
| "347 s → 344 s, ~0 % gain" | The session's prose summary quoted a B1 of 347 s. **347 appears nowhere in the matrix** — the matrix's B1 is **496 s**. Every conclusion drawn from the mis-stated number ("FirstBlockCache ~0×", "we validated almost none of it") was wrong, and the 347 s figure was also filed against `sage-attention-ab.md`, which actually records the Sage arm **rejected before sampling** with no speedup claimed. | Corrected to **496 s → 344 s = 1.44×** at 8 steps and **635 s → 545 s = 1.17×** at 16 steps, from the artifact of record. `receipts/our-acceleration-ab.md` names the correction explicitly. |
| The adapter shelf dropped from the README, and its 8-step LoRA hash wrong | The 8-step LoRA hash in the old README was **63 hex characters** — not a valid SHA-256. The real value is `2339acdf19bfe123f46b971ea35d367a84adb85de43627e1eceafa5a5b2b111e`. | Adapter shelf restored, all three adapters' sizes and hashes verified directly on the weights tree. `receipts/adapter-shelf.md`. |

---

## 4. Not in this repository

* No licence determination. That is the production lead's call and it is deferred.
* No timeline or changelog.
* No raw model weights, no training data, no base-model fine-tunes. The complete weight
  inventory, with every published SHA-256 and what we did to each file, is in
  `receipts/weights.md`.
* No claim that the published ladder was reproduced on our hardware.
* No claim that our 1.44× is comparable to the published 1.54× — different geometry, different
  step count, different machine.
