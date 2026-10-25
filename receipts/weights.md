# Weights — every file this project takes or produces

**Keel ships no weights.** Nothing in this repository is a model. Everything below is either
published by someone else and downloaded by us, or published by us and verified by us.

Two sources agree on the bytes, and both are filed:

1. **The model repository's manifest** — the `siblings` listing for `Comfy-Org/MiniMax-H3` at
   revision `0543966fbdce5ba05709a8f2031c94bdba629b4a`, captured as `source-listing.json` in the
   production runtime record.
2. **Our own download**, hashed on our own box — `receipts/verification.json`.

For the pruned FP8 FL2VA DiT the two agree exactly: manifest LFS SHA-256
`12944c1f7791637e7de12208aef04da82bd26b95271b1b47d817364315ade993`, byte count `20,958,205,608`.
That is the value we hashed on the file we actually downloaded. The same value on both sides is
what makes the rest of this table trustworthy.

## The four weight families

| Family | Files | What it is |
|---|---|---|
| **DiT** — the denoiser | `minimax_h3_{fl2va,ref2va}_*.safetensors` | Two variants of the same 33B transformer: **FL2VA** (first/last frame to video+audio) and **Ref2VA** (reference image/video/audio to video+audio) |
| **Text encoder** | `qwen3vl_32b_minimax_h3_*.safetensors` | Qwen3-VL-32B, conditioning the prompt |
| **VAEs** | `minimax_h3_video_vae_fp16`, `minimax_h3_audio_vae_fp32` | Video decoder and audio decoder — H3 is joint video **and** native stereo audio |
| **Turbo LoRAs** | `minimax_h3_{fl2v,ref2v}_turbo_*.safetensors` | Step-distillation adapters that cut 20 sampling steps to 4 or 8 |

## DiT — the denoiser

| File | Bytes | GB | SHA-256 | What we did |
|---|---:|---:|---|---|
| `minimax_h3_fl2va_bf16.safetensors` | 66,280,487,368 | 66.28 | `907d4add438438ec1544f5240c3b38532ed934fe6be75677a6bbda2a6fdd6182` | **untouched** — we do not use it, and it does not fit |
| `minimax_h3_ref2va_bf16.safetensors` | 66,280,487,368 | 66.28 | `e32c54c1a7b4f5f397f195cea267ccb18806303bb665678c4bee60953bdf3026` | **untouched** — does not fit |
| `minimax_h3_fl2va_int8_convrot.safetensors` | 34,038,892,334 | 34.04 | `7ad4c73e6e378b822ffd1629f27f632d3787d95f5e468e3af958f98c58df96a5` | **untouched** — published as-is |
| `minimax_h3_ref2va_int8_convrot.safetensors` | 34,038,894,550 | 34.04 | `9eef934046a0671bc8a5daf87100705e1478419c574cfde70c50fbe6885f76a9` | **untouched** — published as-is |
| `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 20,958,205,608 | 20.96 | `12944c1f7791637e7de12208aef04da82bd26b95271b1b47d817364315ade993` | **untouched** — **the one Keel runs** |
| `minimax_h3_ref2va_pruned_fp8_scaled.safetensors` | 20,958,205,608 | 20.96 | `f86f2f79ebd2d76eb8eeb46091e83982e6ff51d255747e7b16e92834b392b8e9` | **untouched** — the Ref2VA arm |
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 20,970,379,616 | 20.97 | `e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a` | **untouched** — the INT8 convert path |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | 20,970,379,616 | 20.97 | `9255f52b6677845ad238f20dfaafa94727053694127ab7f255c048f0f9365779` | **untouched** — the INT8 convert path |

**We produced none of these.** Every DiT variant is published by the model repository. "Pruned",
"FP8-scaled" and "INT8 ConvRot" are the publisher's names for their conversions, not ours. Keel's
contribution is knowing which of them to put in which machine, and proving the bytes.

## Text encoder

| File | Bytes | GB | SHA-256 | What we did |
|---|---:|---:|---|---|
| `qwen3vl_32b_minimax_h3_bf16.safetensors` | 51,506,295,256 | 51.51 | `600d567f6a9629c8574e8e7041b199bdd9c59a986afa7906910a81919610607d` | **untouched** — does not fit alongside a BF16 DiT |
| `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 27,141,342,152 | 27.14 | `bc2ced0fbea64757fa9acddccfc0b3f4819d1dcf1da6c124d690d368be283923` | **untouched** — published as-is |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15,687,142,551 | 15.69 | `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6` | **untouched, re-downloaded** — **the one Keel runs** |

### The corrupt download, and what it taught us

The first copy of the NVFP4/AWQ encoder that reached our box was **21,714,795,671 bytes** —
6,027,653,120 bytes larger than the real file. The safetensors header accounted for only
15,687,142,551 bytes of it, and `complete_offset_boundary` was `false`. The header was fine; the
payload behind it was not. Its SHA-256 was
`61f55b01f03e9cd9ec2b10e3084e74519230373135aef5c84ec6b7ec04208340`.

It loads. It produces nothing. It does not error.

A partial file of the same name also appeared on one of the fleet's Sparks — the BF16 DiT at
**35,660,245,251 bytes** against a header declaring **66,280,487,368**, 30,620,242,117 bytes short
and unloadable. That truncated file's size is where an earlier "35.7 GB BF16" claim in this
repository came from.

**The rule both cases establish: quote a checkpoint size from the safetensors header, never from
`stat`.** The header is what the file promises to be; the size on disk is only what survived the
download. The check that catches both is in `receipts/checkpoint-sizes.md`.

Details and the raw log: `receipts/encoder-diagnosis.md`, `receipts/text-encoder-load.log`.

## VAEs

| File | Bytes | GB | SHA-256 | What we did |
|---|---:|---:|---|---|
| `minimax_h3_video_vae_fp16.safetensors` | 5,207,808,496 | 5.21 | `7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522` | **untouched** — 562 fp16 tensors, header-complete, zero trailing bytes |
| `minimax_h3_audio_vae_fp32.safetensors` | 605,254,808 | 0.61 | `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48` | **untouched** — 917 fp32 tensors, header-complete, zero trailing bytes |

## Turbo LoRAs

Step-distillation adapters. Sizes and hashes verified directly on the weights tree.

| File | Bytes | SHA-256 | What we did |
|---|---:|---|---|
| `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` | 1,956,192,992 | `c396a9a06f58399e9df9754b18299818d84a2ddd371724ba48fe4a41221437dc` | **untouched** — published adapter |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | 1,956,193,000 | `2339acdf19bfe123f46b971ea35d367a84adb85de43627e1eceafa5a5b2b111e` | **untouched** — published adapter |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` | 1,956,193,000 | `5b9ab5ade15d0775676d01a907268a69a1468dc6033b3b0d3ded5502f3ebb84c` | **untouched** — published adapter |

These are published too. What this team *did* produce is its own LoRA work, and that is a
different artefact class — trained adapters, with training logs and reload-verification, catalogued
in [`../training/TRAINING.md`](../training/TRAINING.md). No trained adapter ships in this
repository either.

## What this repository ships today

**No weights. Not one byte.** It ships:

* the recipes and the node packs to use the published weights,
* the byte-exact table above so you can verify what you downloaded,
* the hash-check procedure that catches a bad download before it costs you a render,
* and receipts for every number Keel claims.

## The publish-the-weights option — an open question, not a plan

**Keel does not publish weights and this repository does not contain any.** If that ever changes,
here is what it would actually take, so the decision can be made on facts:

| | What it would involve |
|---|---|
| **What** | Hosting the pruned FP8 DiT and the NVFP4 encoder somewhere, and pointing the recipe at that host instead of at `Comfy-Org/MiniMax-H3`. |
| **Size** | ~20.96 GB for the FL2VA DiT, ~15.69 GB for the encoder, ~5.82 GB for both VAEs, ~1.96 GB per turbo LoRA. |
| **Why it might be wanted** | The corrupt-download failure was real and cost a render. A controlled host removes that failure mode. |
| **Why it might not** | These files are already published by the model repository. Re-hosting published weights duplicates a large artefact for no accuracy gain, and it is a redistribution decision rather than a technical one. |
| **What we would need to settle first** | Whether to mirror the published files byte-for-byte or re-emit them; where they would live; how the hash table stays truthful if the mirror diverges from the publisher's copy. |

This is not settled here. It is not scheduled, and nothing in this repository does it.
