# MiniMax H3 — deployment field guide

Self-hosted **MiniMax H3**: omni-modal **video + native stereo audio**, 4–15 s clips at 24 fps. Every clip is H.264 + stereo AAC — not silent video with dubbed TTS. Weights stay off git.

## What H3 is

- Joint video/audio diffusion. Two DiTs share one encoder + VAEs: **FL2VA** (`t2va` / `fl2va`) and **Ref2VA** (`ref2va`).
- Open weights = **H3-Base at ~768p**. H3-Context-IR (prompt orchestration) and H3-Regenerate-2K are hosted APIs, not part of the open dump.
- **Sizes, byte-exact** (full table in [`../receipts/checkpoint-sizes.md`](../receipts/checkpoint-sizes.md)):

  | What | Bytes | GB |
  |---|---:|---:|
  | BF16 FL2VA DiT | 66,280,487,368 | 66.28 |
  | BF16 Ref2VA DiT | 66,280,487,368 | 66.28 |
  | BF16 Qwen3-VL-32B encoder | 51,506,295,256 | 51.51 |
  | Video VAE fp16 + audio VAE fp32 | 5,813,063,304 | 5.81 |
  | **Full BF16 checkout (both DiTs + encoder + VAEs)** | **189,880,333,296** | **189.88** |
  | **One BF16 partition (one DiT + both VAEs)** | **72,093,550,672** | **72.09** |

  The pruned FP8-scaled build this repo runs brings each DiT to **21.0 GB** and the NVFP4/AWQ
  encoder to **15.7 GB** — 42.4 GB for a DiT, an encoder and both VAEs, which is what actually
  fits in a Spark's 121 GB visible unified memory. An earlier revision of this guide said "one
  partition is ~135 GiB BF16"; that figure was wrong and has been corrected.
- Weights: [MiniMaxAI/MiniMax-H3](https://huggingface.co/MiniMaxAI/MiniMax-H3) (gated). Serve via the vLLM-Omni recipe, SGLang, Diffusers — or ComfyUI with this repo's node packages.

## Do not start with a single 3090 and hope

| Hardware | Honest path | Notes |
|---|---|---|
| **DGX Spark (GB10, 128 GB unified)** | ComfyUI + this repo's stack | 864×480 × 124 frames is the benchmarked workload; 362 frames is the practical ceiling for one Spark |
| **2× RTX 5090 32 GB** + ~384 GiB RAM | vLLM-Omni DLO, `--task-type fl2va`, 1344×768 | Validated low-memory TP2 |
| **2× RTX 4090 / 3090 24 GB** + ≥200 GiB RAM (384 GiB recommended) | Same DLO, 12 resident layers, **1024×576** start | 3090 ≈ 4090 VRAM. Slow. FL2VA only |
| **1× GPU + CPU offload** | `--enable-cpu-offload --task-type fl2va` | Accuracy path; needs huge host RAM; not a 3090-only box |
| **4× 80 GB+** (H100/H200/B200) | No-offload, both DiTs, `/v1/videos` | Production-ish |
| 1× 3090 24 GB alone | **Not a first target** | Will crawl or OOM unless offload + lots of system RAM is measured |

Quantized community GGUFs exist; they are not the MiniMax-published BF16 serve path. Treat them as a later experiment, not a first target.

## First success looks like

A serve call returns H.264 at 24 fps **with stereo audio** (check with `ffprobe`) — or, on the ComfyUI path, the forward-proof in [`../receipts/forward-receipt.json`](../receipts/forward-receipt.json) reproduces: 124 frames, video+audio decode, clean exit.
