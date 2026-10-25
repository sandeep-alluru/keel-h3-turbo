# Checkpoint sizes — byte-exact, and where each number came from

Two sources agree on the bytes that matter here, and both are filed:

1. **The model repository's own manifest** — the `siblings` listing for `Comfy-Org/MiniMax-H3`
   at revision `0543966fbdce5ba05709a8f2031c94bdba629b4a`, captured as
   `source-listing.json` in the launch lane's runtime record.
2. **Our own download**, hashed on our own box — `receipts/verification.json`.

For the pruned FP8 DiT the two agree exactly: the manifest's LFS SHA-256 is
`12944c1f7791637e7de12208aef04da82bd26b95271b1b47d817364315ade993` and the byte count is
`20,958,205,608`. The same value is what `receipts/verification.json` recorded after we hashed
the file we actually downloaded. That is the check that makes the rest of the table trustworthy.

## Diffusion models

| File | Bytes | GB | Notes |
|---|---:|---:|---|
| `minimax_h3_fl2va_bf16.safetensors` | 66,280,487,368 | 66.28 | FL2VA, full precision |
| `minimax_h3_ref2va_bf16.safetensors` | 66,280,487,368 | 66.28 | Ref2VA, full precision |
| `minimax_h3_fl2va_int8_convrot.safetensors` | 34,038,892,334 | 34.04 | |
| `minimax_h3_ref2va_int8_convrot.safetensors` | 34,038,894,550 | 34.04 | |
| `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 20,958,205,608 | 20.96 | **the one we run** |
| `minimax_h3_ref2va_pruned_fp8_scaled.safetensors` | 20,958,205,608 | 20.96 | |
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 20,970,379,616 | 20.97 | |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | 20,970,379,616 | 20.97 | |

## Text encoder

| File | Bytes | GB | Notes |
|---|---:|---:|---|
| `qwen3vl_32b_minimax_h3_bf16.safetensors` | 51,506,295,256 | 51.51 | |
| `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 27,141,342,152 | 27.14 | |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15,687,142,551 | 15.69 | **the one we run** |

## VAEs

| File | Bytes | GB | Notes |
|---|---:|---:|---|
| `minimax_h3_video_vae_fp16.safetensors` | 5,207,808,496 | 5.21 | complete, 562 fp16 tensors, zero trailing bytes |
| `minimax_h3_audio_vae_fp32.safetensors` | 605,254,808 | 0.61 | complete, 917 fp32 tensors, zero trailing bytes |
| **both VAEs together** | **5,813,063,304** | **5.81** | what every row in the residency table below adds |

---

## Why the pruned FP8 pair is the one that fits

A DGX Spark shows 121 GB of its 128 GB unified memory to the runtime. The combinations that
matter:

| DiT | Encoder | Video VAE | Audio VAE | Sum | Fits 121 GB? |
|---|---|---|---|---:|---|
| BF16 66.3 | BF16 51.5 | 5.2 | 0.6 | 123.6 GB | **No** — 115.1 GiB of payload plus activations |
| BF16 66.3 | NVFP4 15.7 | 5.2 | 0.6 | 87.8 GB | Yes, with headroom |
| INT8 ConvRot 34.0 | NVFP4 15.7 | 5.2 | 0.6 | 55.5 GB | Yes, comfortably |
| **Pruned FP8 21.0** | **NVFP4 15.7** | 5.2 | 0.6 | **42.4 GB** | **Yes — this is the production pair** |
| Pruned INT8 ConvRot 21.0 | NVFP4 15.7 | 5.2 | 0.6 | 42.4 GB | Yes |

This is also why NVIDIA's own GB10 recipe uses a pruned FP8 DiT and an FP8 Qwen3-VL: on the
unified-memory side of the machine, precision is not a preference, it is a residency requirement.
NVIDIA's published GB10 figure (710.6 s → 181.3 s, 3.92×) is a number produced on the FP8 pair.

## The corrupt encoder, and the fix

The first copy of `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` that reached our box was
**21,714,795,671 bytes** — 6,027,653,120 bytes larger than the real file. The safetensors header
accounted for only 15,687,142,551 bytes of it, and `complete_offset_boundary` was `false`. The
header was fine; the payload behind it was not. Details and the log line are in
`receipts/encoder-diagnosis.md` and `receipts/text-encoder-load.log`.

The re-download landed at the exact expected size and hashes clean. The keeper and forward
receipts both reference the clean file by name
(`qwen3vl_32b_minimax_h3_nvfp4_awq-fresh-0543966f.safetensors`).

## What we did not do

We did not produce the pruned FP8 checkpoints ourselves and we did not quantise anything — they
are published by the model repository, and we verified the bytes we downloaded against the
published hash. Anything this repo claims about them is a claim about the *download*, never about
the quantisation.
