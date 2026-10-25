# Checkpoint sizes — byte-exact, and where each number came from

Two sources agree on the bytes that matter here, and both are filed:

1. **The model repository's own manifest** — the `siblings` listing for `Comfy-Org/MiniMax-H3`
   at revision `0543966fbdce5ba05709a8f2031c94bdba629b4a`, captured as
   `source-listing.json` in the production's runtime record.
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

## Where "35.7 GB" came from — and why it is not the BF16 size

An earlier revision of this repository claimed the BF16 DiT was **35.7 GB**. That number is real,
and it is the size of a **broken partial download**.

On the second Spark in the fleet there is a file called
`minimax_h3_fl2va_bf16.safetensors` that is **35,660,245,251 bytes** on disk. Its own safetensors
header declares **66,280,487,368 bytes** across 535 tensors (BF16 522, F32 13). The file is
**30,620,242,117 bytes short** — **30.6 GB** short. It cannot load, and nothing on that box can load it.

So the sequence was: a download stopped part-way, the partial file sat on disk with the right
name, `ls -l` was read as the checkpoint size, and 35.7 GB was written down as the size of the
BF16 model. It is not. The BF16 DiT is 66.28 GB, and the pruned FP8 build cuts it to 20.96 GB —
a **68 % reduction**, not the 41 % that "35.7 → 21.0" implies.

**The rule this establishes: quote a checkpoint size from the safetensors header, never from
`stat`.** The header is what the file promises to be; the file size on disk is only what
survived the download. The check is the same one that caught the corrupt encoder:

```python
import json, struct, pathlib

p = pathlib.Path("minimax_h3_fl2va_bf16.safetensors")
with p.open("rb") as fh:
    n = struct.unpack("<Q", fh.read(8))[0]
    header = json.loads(fh.read(n))
declared = header.get("__metadata__", {}).get("total_size") or max(
    (v["data_offsets"][1] for k, v in header.items() if k != "__metadata__"), default=0
)
print(f"on disk {p.stat().st_size:,}  header declares {declared:,}  "
      f"{'COMPLETE' if p.stat().st_size >= declared else 'TRUNCATED'}")
```

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

## The residency totals, in GB

The front page quotes these as GB. They are sums of the byte-exact figures above.

| DiT | Encoder | + VAEs | Total (bytes) | Total (GB) | Fits 121 GB? |
|---|---|---|---:|---:|---|
| BF16 66.28 GB | BF16 51.51 GB | 5.81 GB | 123,599,845,928 | **123.60 GB** | **No** |
| BF16 66.28 GB | NVFP4 15.69 GB | 5.81 GB | 87,780,693,223 | **87.78 GB** | Yes |
| INT8 ConvRot 34.04 GB | NVFP4 15.69 GB | 5.81 GB | 55,539,098,189 | **55.54 GB** | Yes |
| **Pruned FP8 20.96 GB** | **NVFP4 15.69 GB** | 5.81 GB | **42,458,411,463** | **42.46 GB** | **Yes — the production pair** |

## The corrupt encoder, and the fix

The first copy of `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` that reached our box was
**21,714,795,671 bytes** — 6,027,653,120 bytes larger than the real file. The safetensors header
accounted for only 15,687,142,551 bytes of it, and `complete_offset_boundary` was `false`. The
header was fine; the payload behind it was not. Details and the log line are in
`receipts/encoder-diagnosis.md` and `receipts/text-encoder-load.log`.

The re-download landed at the exact expected size and hashes clean. The shot and forward
receipts both reference the clean file by name
(`qwen3vl_32b_minimax_h3_nvfp4_awq-fresh-0543966f.safetensors`).

## What we did not do

We did not produce the pruned FP8 checkpoints ourselves and we did not quantise anything — they
are published by the model repository, and we verified the bytes we downloaded against the
published hash. Anything this repo claims about them is a claim about the *download*, never about
the quantisation.
