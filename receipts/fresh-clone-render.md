# Fresh-clone render — the shipped workflow, end to end

This is the receipt for the run that proves the headline path works on a clean machine: a fresh
clone of the pushed repository, the documented installer, the published weights, and the shipped
workflow rendering a complete clip.

**Measured here.** 2026-10-25, on a DGX Spark (GB10, `sm_121`, 121 GB of visible unified memory).

---

## 1 — The clone

| | |
|---|---|
| Origin | `ssh://clawer-samurai-1@100.90.129.41/.../release-staging/minimax-h3-local-engine` |
| Commit | `3a24293` — "a benchmarks page, with a chart for every table" |
| Tracked files | 150 |
| Claim checker | `python3 scripts/check_receipts.py` → six groups `ok`, exit 0 |

The render was repeated against `a1d0cb0` — "the fresh-clone render, filed as a receipt", 151
tracked files, checker green — and produced the same output file and the same six skipped steps.
The two commits differ in the README's wording, the clip index and this receipt; the workflow file,
the installer and the node packs are identical between them.

## 2 — The install

The installer the repository ships, run against a ComfyUI tree that did not exist beforehand:

```bash
bash custom_nodes/H3-SolAttn-SM121/install.sh --comfy-dir <fresh dir> --skip-weights
```

| | |
|---|---|
| Exit code | 0 |
| Python / torch | 3.12.3, torch 2.14.1+cu130 |
| Device | NVIDIA GB10, `sm_121` |
| Triton TMA descriptors | available |
| ComfyUI | v0.30.1, cloned by the installer |
| Landed | `ComfyUI_sol-attn_Blackwell` (Sol-Attn, FirstBlockCache, batched VAE), `ComfyUI-SolAttn_triton`, the H3 native nodes, the launcher and the tuned workflow |

## 3 — The weights, checked against the published hashes

Every file was hashed before the run. The digest below is the publisher's, from
`receipts/weights.md`.

| File | Bytes | SHA-256 | Match |
|---|---:|---|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 20,970,379,616 | `e889202c41dafb67b10d67b97f0d8541508036a6090af23425a5c2615d03c47a` | yes |
| `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 20,958,205,608 | `12944c1f7791637e7de12208aef04da82bd26b95271b1b47d817364315ade993` | yes |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15,687,142,551 | `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6` | yes |
| `minimax_h3_video_vae_fp16.safetensors` | 5,207,808,496 | `7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522` | yes |
| `minimax_h3_audio_vae_fp32.safetensors` | 605,254,808 | `8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48` | yes |

The first of these is the denoiser the shipped workflow names. It is **20,970,379,616 bytes** —
the pruned INT8 ConvRot build. The 34,038,892,334-byte figure belongs to the non-pruned
`minimax_h3_fl2va_int8_convrot.safetensors`, a different file in the same family.

## 4 — The run

`workflows/h3-fullstack.json`, straight out of the fresh clone, posted to a headless ComfyUI on
`127.0.0.1:8191`.

| | |
|---|---|
| Graph | `UNETLoader` → `SolAttnPatch` → `MiniMaxH3ImageToVideo` → `SamplerCustomAdvanced` → `H3FirstBlockCache` → `VAEDecode` + `VAEDecodeAudio` → `CreateVideo` → `SaveVideo` |
| Geometry | 864×480, 124 frames, 24 fps |
| Steps | 20, `res_multistep` / `simple`, seed 46 |
| `SolAttnPatch` | tau 1.3, start 0.2, end 0.9, min tokens 4096, `int8_qk`, `use_tma` |
| `H3FirstBlockCache` | threshold 0.08, `start_step` 3, `end_dense_steps` 2, `max_consecutive_skips` 2 |
| Batched VAE decode | installed — the log reads `batched spatial-tile decode installed (1.66x on GB10)` |
| Sol-Attn kernel | `sparse (1, 15455, 56, 128) tau=1.3 int8 tma` |

### The FirstBlockCache skip list

The cache logged a decision for every step:

```
[H3-FBC] steps computed=14 skipped=6
```

The six skipped steps are **6, 7, 9, 10, 12 and 13**. The published ladder records the same six —
"with the guards (`start_step=3`, `end_dense_steps=2`, `max_consecutive_skips=2`) this skips 6 of 20
steps — steps 6, 7, 9, 10, 12, 13" (`receipts/bench-results.md`).

That is a behavioural match, not a timing match: the cache reaches the same decisions on this
stack, at the same seed, as the run that produced the published ladder.

## 5 — The output

| | |
|---|---|
| File | `h3_fullstack_00001_.mp4` |
| Bytes | 520,124 |
| Video | H.264, 864×480, 124 frames, 24 fps |
| Audio | AAC, 163 frames |
| Duration | 5.166688 s |
| SHA-256 | `5d4ac7083ec2ac01d709ec82c47d87209239c412919cc809c312d3c287460d2d` |

An earlier run of the same workflow at the same settings, against the same weights, produced a
**byte-identical** file — the same SHA-256. The render is reproducible on this stack.

## 5b — Three runs, one file

| Run | Commit | Prompt execution | Output SHA-256 |
|---|---|---:|---|
| 1 | `3a24293` | 204.78 s | `5d4ac708…` |
| 2 | `a1d0cb0` | 198.32 s | `5d4ac708…` |
| 3 | `3a24293`, repeated | 230.87 s | `5d4ac708…` |

Three runs, three wall times, one file. The wall time moves with the machine's load; the output
holds still.

## 6 — The wall time, and the conditions it was taken under

| | |
|---|---|
| Prompt execution | 198.32 s on the `a1d0cb0` clone; 204.78 s and 230.87 s on two earlier runs |
| Wall clock, including the queue | 210 s |
| GPU | NVIDIA GB10, 0 % utilisation at the start, 49 °C, SM clock 2405 MHz |
| RAM | 121 GB total, 64 GB available |

Two other CUDA processes were resident for the whole run:

| PID | Process | Memory held |
|---|---|---:|
| 2399 | `llama-server` (an unrelated model server) | 4,120 MiB |
| 1830035 | an idle ComfyUI on another tree | 40,780 MiB |

**What that means for this figure.** The published ladder in `receipts/bench-results.md` was taken
with `nvidia-smi --query-compute-apps` empty, and it says so: "every row below was taken with no
competing CUDA process". This run had 44.9 GB of unified memory held by other work, which changes
the memory headroom the render runs in. So this wall time is filed here as **a run time**, and it
sits outside the speed tables on the front page and in `docs/benchmarks.md`. A benchmark-comparable
figure for this stack needs the process list empty.

The parts of this receipt that do not depend on the machine's load are the ones worth carrying
forward: the install path, the five weight digests, the six skipped sampling steps, and the output
digest.
