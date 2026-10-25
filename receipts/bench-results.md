# Speed ladder — published benchmark, reproduced verbatim

> **Provenance — read this first.**
>
> Every table below was measured by the author of the community Sol-Engine port for a single
> DGX Spark, on **their** host `spark-13b3`, and published in their repository. That port is
> vendored here unchanged under `custom_nodes/H3-SolAttn-SM121/`; this file reproduces their
> published benchmark **as the published benchmark it is** — it is not a measurement this team
> took, and it is not presented as one anywhere in this repository.
>
> | | |
> |---|---|
> | Source repository | `drowzeys/keys-SM121-Optimized-MiniMax-H3-Nvidia-Sol-Engine-Kijai-SolAttn_Triton-Single-DGX-Spark` |
> | Source file | `bench/results.md` |
> | Source commit | `7e3db54a0ecf7fa524ee3b01ea9ef7092b0e3318` (2026-08-16) |
> | Upstream host | `spark-13b3` (not ours) |
> | Upstream hardware | NVIDIA DGX Spark, GB10, `sm_121`, 128 GB unified |
> | Re-measured by this team? | **No.** |
> | Where our own numbers live | `receipts/verification.json`, `receipts/forward-receipt.json`, `receipts/shot-receipt.json`, `receipts/sage-attention-ab.md`, `receipts/spillway-shots.md`, `receipts/checkpoint-sizes.md` |
> | Full number-by-number map | `receipts/PROVENANCE.md` |
>
> A note on the two "vs dense" columns: this file mixes end-to-end ratios and per-step ratios
> in one column. `14.40 / 9.72 = 1.48×` is a per-step ratio; `312.7 / 215.7 = 1.45×` is an
> end-to-end ratio for a different arm. The upstream table prints `1.45×` on the FirstBlockCache
> end-to-end row and `1.48×` on the FirstBlockCache per-step row; both are right for their own
> column. We keep the file byte-identical to upstream below rather than "fixing" a third
> party's table.

# Raw benchmark data

## Machine

| | |
|---|---|
| Host | `spark-13b3`, NVIDIA DGX Spark |
| GPU | GB10, `sm_121` (compute capability 12.1), 3003 MHz max SM |
| Memory | 128 GB unified (121 GB visible) |
| Arch / OS | aarch64, DGX OS 7.5.0, kernel 6.17 |
| CUDA / torch | CUDA 13.0, torch 2.11.0+cu130 |
| ComfyUI | v0.30.1 |

## Workload

MiniMax-H3 FL2VA pruned INT8 + Qwen3-VL-32B NVFP4-AWQ text encoder, video VAE fp16 +
audio VAE fp32. 864×480, 124 frames (5.17 s @ 24 fps), 20 steps, `res_multistep` /
`simple`, joint video+stereo-audio output. Same prompt and seed 46 across the ladder
unless noted.

**Hygiene:** every row below was taken with no competing CUDA process
(`nvidia-smi --query-compute-apps` empty), GPU ≤ 75 °C, SM ≥ 2398 MHz. Runs taken
while two `cuBitCrack` processes held 95 % GPU are excluded and listed separately.

## End-to-end (prompt → finished mp4)

| Config | Wall | vs dense |
|---|---:|---:|
| Dense (stock ComfyUI, no accelerations) | 312.7 s | 1.00× |
| FirstBlockCache only | 215.7 s | 1.45× |
| Full stack (kijai Sol-Attn + FBC + batched VAE) | **202.5 s** | **1.54×** |

## Denoising cost per step

| Config | s/step | vs dense |
|---|---:|---:|
| Dense | 14.40 | 1.00× |
| Sol-Attn only (kijai, tau 1.3, int8+TMA, 6 dense steps) | 11.11 | 1.30× |
| Sol-Attn only (KingGore, tau 1.0, all steps sparse) | 10.88 | 1.32× |
| FirstBlockCache only (thr 0.08) | 9.72 | 1.48× |
| kijai Sol-Attn + FBC | 8.09 | 1.78× |
| Full stack (+ batched VAE decode) | 8.39 | 1.72× |

`8.09` vs `8.39` is run-to-run variance (different seeds, ±4 %); the batched VAE
changes decode, not sampling. Treat them as the same sampling configuration.

## Isolated component measurements

**Batched VAE tile decode**, one temporal chunk at 864×480, warm:

| | Time | |
|---|---:|---|
| Sequential tiles (stock) | 4.871 s | |
| Batched same-shape tiles | 2.933 s | **1.66×** |

Output is `allclose`, not bit-identical — batch size changes fp16 kernel selection.
Max abs diff 1.56e-2, mean 5.29e-4 on a [-1,1] pixel range (≈0.8 % worst pixel).

**Sol-Attn kernel numerics vs dense SDPA** (B=1, S=4160, H=56, D=128, bf16, tau=1.0),
cosine similarity, higher is better — 1.0 is identical:

| Kernel | cos vs SDPA | verdict |
|---|---:|---|
| KingGore Triton (`triton_ref`) | 0.99998 | exact enough |
| kijai bf16 pointer | 0.99995 | exact enough |
| kijai bf16 TMA | 0.99995 | exact enough |
| kijai INT8 QK | 0.99995 | exact enough |
| **torch `flex_attention`** (sm_121) | **0.9167 @ S=1536, 0.9688 @ S=4096** | **BROKEN — do not use** |

The flex_attention path compiles and runs without error. It is simply wrong on this
architecture, and the error compounds across 50 blocks × 20 steps into visible noise.

## FirstBlockCache behaviour at 20 steps

Per-row diff ratio over the trailing 60 % of sequence rows, threshold 0.08:

| step | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| ratio | .179 | .137 | .113 | .097 | .084 | .075 | .074 | .071 | .070 | .067 |

| step | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|---|
| ratio | .069 | .072 | .074 | .078 | .091 | .109 | .132 | .167 | .249 |

U-shaped: high at both ends, minimum around step 10. With the guards
(`start_step=3`, `end_dense_steps=2`, `max_consecutive_skips=2`) this skips
**6 of 20 steps** — steps 6, 7, 9, 10, 12, 13.

## Longer clips

15.1-second clip (362 frames, the model's trained maximum), same settings, full stack
minus batched VAE, measured before the final tuning:

| | |
|---|---:|
| Sampling | 27 m 42 s (83.1 s/step) |
| Total | 31 m 34 s |
| Memory floor | 10–13 GB free of 121 GB |

2.9× the frames costs 6.5× per step — attention scaling, even sparsified. 864×480 ×
362 frames is the practical ceiling for a single 128 GB Spark.

## Excluded: contended runs

Kept for the record — these were taken with two `cuBitCrack` processes at 95 % GPU
and are **not** comparable to anything above:

| Config | s/step | Wall |
|---|---:|---:|
| Sol-Attn (KingGore) | 20.77 | 476.5 s |
| Sol-Attn + FBC | 14.56 | 352.6 s |

The A/B ratio between those two (1.35× e2e) is still valid — same thermal state,
back to back — but the absolute numbers are inflated ~1.9×.
