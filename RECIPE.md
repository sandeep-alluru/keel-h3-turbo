# Single-shot agent recipe

Paste this whole file to a coding agent (Claude Code, Codex, Cursor) sitting on a
DGX Spark. It is written to be executed top-to-bottom without asking questions.
Every number in it was measured on the machine described in `bench/results.md`.

**Target:** NVIDIA GB10 / DGX Spark, `sm_121`, 128 GB unified memory, aarch64, CUDA 13.
**Goal:** MiniMax-H3 text/image→video+audio in ComfyUI at ~200 s per 5-second 864×480 clip,
down from ~313 s stock.

---

## Why each piece speeds it up

H3 is a 33 B dense single-stream DiT: text, audio and video latents are packed into
**one** sequence (38,247 rows at 1344×768/124f) with full self-attention over all of
it. There is no CFG branch to drop and no cross-attention to cache. That shape decides
everything — attention is ~70 % of the hot path, so the wins come from (a) making
attention sparse, (b) not running the network at all on some steps, and (c) fixing
launch-bound work outside the DiT.

| # | Optimization | Origin | Mechanism | Measured on GB10 |
|---|---|---|---|---|
| 1 | **Sol-Attn** | NVIDIA Sol-Engine (paper + kernels), packaged by KingGore / kijai | Routes each query block to only the top-scoring KV blocks; the rest is approximated by a pooled/compensating term. Route density ~0.225 measured by NVIDIA. | **14.40 → 10.88 s/step (1.32×)** |
| 2 | **FirstBlockCache** | NVIDIA Sol-Engine `cache_line.py`, ported here to ComfyUI | Runs block 0 every step; if its residual barely changed vs the previous step, skip the other 49 blocks and re-apply the cached tail residual. | **14.40 → 9.72 s/step (1.48×)** |
| 3 | **Batched VAE tile decode** | NVIDIA Sol-Engine `vae_shard.py`, ported here | Stock ComfyUI pushes ~10 spatial tiles through the 36-layer ViT decoder one launch at a time; batching same-shape tiles fills the GPU. | **4.87 → 2.93 s/chunk (1.66×)** on decode |
| 4 | **INT8 QK + TMA** (kijai) | kijai/ComfyUI-SolAttn_triton | Sage-style smoothed-K INT8 in the exact branch (bit-preserving for softmax) + TMA descriptors on Blackwell. Lets you keep 6/20 steps dense *and* the conditioning rows exact at the same speed as tau=1.0 everywhere. | quality headroom at equal speed |
| 5 | **AdaLN precompute** | NVIDIA Sol-Engine `adaln.py` | ~13 B of H3's 33 B lives in AdaLN branches whose modulation outputs can be precomputed. | **already in the pruned checkpoint** — free |

Stacked: **312.7 s → 202.5 s end-to-end (1.54×)**, **14.40 → 8.39 s/step (1.72×)**.

**Not applicable on one Spark** (documented so you don't chase them):
context parallelism / Ulysses (needs ≥2 GPUs with fast interconnect — NVIDIA used
503 GB/s NVLink), the fused-QKV single-collective change and the Triton relayout
kernels (they exist to feed that all-to-all), and most of the elementwise DiT
fusions (NVIDIA's own README calls ~3 % the honest ceiling, and ComfyUI's
`_mod_gate`/`_mod_scale_shift` already fuse in-place per segment).

---

## Execute

```bash
git clone https://github.com/drowzeys/<REPO>.git && cd <REPO>
./install.sh                    # add --skip-weights if you already have them
~/comfy/h3-comfy-launch.sh      # serves :8188
```

Then render headlessly:

```bash
curl -X POST http://127.0.0.1:8188/prompt -H 'Content-Type: application/json' \
  -d "{\"prompt\": $(cat ~/comfy/h3-fullstack.json)}"
```

Node graph the workflow builds (all four accelerations active):

```
UNETLoader ─► SolAttnPatch (kijai) ─► H3FirstBlockCache ─┬─► BasicGuider ──┐
                                                          └─► BasicScheduler┤
CLIPLoader ─────► MiniMaxH3ImageToVideo ──────────────────────────────────► SamplerCustomAdvanced
VAELoader(video) ┘        │                                                        │
VAELoader(audio) ─────────┴──────────────────► VAEDecode + VAEDecodeAudio ◄────────┘
                                                        └► CreateVideo ► SaveVideo
```

## Settings that matter

| Knob | Value | Why |
|---|---|---|
| `SolAttnPatch.tau` | `1.3` | kijai's scale; ~16 % blocks exact at 1.0, ~7 % at 1.5 |
| `SolAttnPatch.start_percent` | `0.2` | first 20 % of the schedule dense — early steps set global structure |
| `SolAttnPatch.sink_conditioning` | `exact_kv_and_rows` | keeps the packed text/audio rows exact; audio degrades first otherwise |
| `SolAttnPatch.int8_qk` / `use_tma` | `true` / `true` | verified cos 0.99995 vs SDPA on sm_121 |
| `H3FirstBlockCache.threshold` | `0.08` | NVIDIA's value; skips 6/20 steps here |
| `H3FirstBlockCache.start_step` | `3` | never cache before the image exists |
| `H3FirstBlockCache.end_dense_steps` | `2` | last steps carry fine detail |
| `H3FirstBlockCache.max_consecutive_skips` | `2` | bounds drift on short schedules (NVIDIA tuned for 50 steps, not 20) |
| sampler / scheduler | `res_multistep` / `simple`, 20 steps | ComfyUI H3 template default |
| frame count | `17k + 5` (124 ≈ 5 s) | model's grid; trained range 124–362 |

## Traps that cost real time

1. **`--use-sage-attention` produces pure noise with H3.** Upstream issue Comfy-Org/ComfyUI#15263.
2. **`torch.nn.attention.flex_attention` is silently WRONG on sm_121** (torch 2.11.0+cu130):
   compiles fine, no error, cosine similarity only 0.92–0.97 vs SDPA. It corrupts every
   layer and looks like a bad checkpoint. Always numerically check a kernel on this arch:
   `F.cosine_similarity(out.flatten(0,2), ref.flatten(0,2), dim=-1).mean() >= 0.999`.
3. **H3 transformer blocks mutate their input in place** (`x[a:b].addcmul_(...)`) and return
   the *same tensor object*. Any cache that computes `output - input` gets exactly zero,
   concludes nothing ever changes, skips everything, and emits checkerboard noise.
   Clone before the block and after block 0.
4. **NVIDIA's cache metric is diluted on H3.** A global mean ratio is dominated by the
   packed text/audio prefix rows, which have outlier magnitudes; it reads ~0.05 when the
   video rows are at 0.18. Use a per-row ratio over the trailing 60 % of rows.
5. **Their threshold assumes 50 steps.** At 20 steps the diff-ratio curve is U-shaped
   (0.18 → 0.066 at step 10 → 0.25), so a bare threshold skips the wrong places. Hence
   `start_step` / `end_dense_steps` / `max_consecutive_skips`.
6. **Benchmarking on a busy GB10 lies.** A background CUDA job (in our case two
   `cuBitCrack` processes) both steals SMs and heats the chip: 10.88 → 20.77 s/step,
   which reads exactly like thermal throttling. Check
   `nvidia-smi --query-compute-apps=pid,used_memory --format=csv` before trusting any number.
7. **ComfyUI caches identical graphs.** Change the seed or you will "measure" a cache hit.

---

## Appendix: running NVIDIA's own Sol-Engine code (measured, not speculated)

"Integrating Sol-Engine" is three separable things. Only one of them works on a
single Spark, and it isn't the one people assume.

### 1. The official kernel package — works, undocumented

`sol-attn` 0.5.0 from `techniques/sparse_backends/` ships CuTe kernels for
`sm_90`, `sm_100`, `sm_120` only. `sm_121` is absent from the table — but
`_backend_for_arch()` falls back to the package's own bundled `triton_ref` for
any capability ≥ 8.0. So NVIDIA's real implementation **does** run on GB10:

```bash
pip install -e ~/comfy/sana-sol-engine/techniques/sparse_backends
python3 -c "import torch;from sol_attn.interface import _backend_for_arch;\
print(_backend_for_arch(tuple(torch.cuda.get_device_capability())))"   # -> triton
```

Measured at an H3-shaped call (B=1, S=4160, H=56, D=128, bf16, tau=1.0):

| Kernel | Time | cos vs SDPA | vs dense |
|---|---:|---:|---:|
| dense SDPA | 5.74 ms | 1.00000 | 1.00× |
| **NVIDIA official `sol_attn`** | 3.51 ms | 0.99995 | 1.63× |
| kijai Triton (+TMA) | 3.33 ms | 0.99995 | 1.72× |

This stack keeps kijai as the default — 5 % faster, plus the H3 conditioning
sink, sigma-window gating and INT8 branch that the reference kernel doesn't have.
NVIDIA's package is worth installing as a cross-check oracle.

### 2. The Sol-Engine runtime — does not fit

It is SGLang + a vendored diffusers (PR #14355) expecting **bf16** checkpoints:
DiT 66.3 GB + Qwen3-VL-32B encoder 51.5 GB = 118 GB of weights, and NVIDIA's own
single-GPU baseline row peaks at **141 GB**. A 128 GB Spark (121 GB usable) cannot
hold it, which is exactly why this repo ports the *techniques* into ComfyUI's
quantized path instead of running their driver.

### 3. Context parallelism over a Spark fabric — measured, and mostly a loss

Ulysses all-to-all traffic for H3 at 864×480 (packed sequence 15,455 rows,
56 heads × 128, bf16, 50 layers) is **11.1 GB per rank per step at CP=2** and
8.3 GB at CP=4.

Real measured fabric throughput between two Sparks over the 200G ConnectX-7 link:
**5.52 GB/s** (45 Gbit/s of a nominal 200 Gbit link, plain TCP). NVIDIA's 3.97×
was measured on 503 GB/s NVLink — **91× more interconnect**.

| Topology | Compute | Comms | Total | vs this repo's single node (8.39) |
|---|---:|---:|---:|---:|
| CP=2 @ 5.5 GB/s | 7.20 s | 2.01 s | 9.21 s | **0.91× — slower** |
| CP=4 @ 5.5 GB/s | 3.60 s | 1.51 s | 5.11 s | 1.64× |
| CP=4 @ 20 GB/s (if RDMA ≫ TCP) | 3.60 s | 0.42 s | 4.02 s | 2.09× |

**CP=2 is a loss at any bandwidth we can measure.** CP=4 is a real but modest win
that costs four nodes and 4 × 118 GB of bf16 weights. Before attempting it,
benchmark **NCCL/RDMA** rather than TCP — the entire case rests on whether the
fabric goes meaningfully above 5.5 GB/s.

If you want more throughput from several Sparks, `scripts/h3-dispatch.py` gives
near-linear scaling by rendering whole clips per node — no interconnect involved.
