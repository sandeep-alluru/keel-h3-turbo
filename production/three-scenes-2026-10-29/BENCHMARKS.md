# Benchmarks: three Keel scenes on one DGX Spark (2026-10-29)

Every number below is computed by `the job's make_pack.py` from the receipt files. Run it again to reproduce them.

## Receipts
| file | what it proves |
|---|---|
| `receipts/spark2-8188-history.json` | ComfyUI `/history` (filtered to these 23 prompts) from spark2 :8188, a read-only GET at 2026-10-29 ~10:01 CDT. Holds the `execution_start` and `execution_success` timestamps (ms) for each prompt. |
| `receipts/attempts-extracted.json` | Per shot: prompt, seed, steps, size, frames, models, prompt id, and the start and end ms. |
| `receipts/spark2-attempts.md5` | md5 of every attempt on spark2. Our copies in `_src/attempts/` match them. |
| `receipts/spark2-refs.txt` | sha256 and mtime of every reference image on spark2. |
| `receipts/timeline-{forest,eagle,dragon}.json` | Frame match of each final against the attempts: per-frame best match, then segments with in/out points and speed (`build/frame_match.py`). |
| `receipts/ref-vs-frames.json` | Which reference images are the previous shot's last frame. |
| `receipts/spark2-model-files.txt` | Byte sizes of the four weight files the graph loads. The DiT is 20,958,205,608 bytes (20.96 GB), the size of Keel's pruned FP8 DiT in the keel-h3-turbo README Trim table. The encoder is `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`, 21,714,795,671 bytes on disk; Keel's README names this exact byte count as the encoder file whose header holds 15.69 GB. So these shots ran on Keel's 42.46 GB weight set. |
| `receipts/spark2-comfy-nodes-gpu.txt` | `nvidia-smi` reads NVIDIA GB10 and `/etc/dgx-release` reads DGX Spark. Also the node packs installed on that ComfyUI. |

## Definition
**GPU time per shot** is ComfyUI `execution_success - execution_start` for that prompt: one MiniMax H3 run, from sampling through the VAE decode to the saved mp4. Queue wait is not included. The shots ran one after another on one GPU, so the per-shot times add up.

## Per scene
| scene | finished length | shots | attempts (retries) | GPU time | GPU s per finished s |
|---|---|---|---|---|---|
| Forest chase | 30.000 s | 6 | 6 (0) | 3533.9 s = 58.9 min | 117.8 |
| Eagle hunt | 36.042 s | 7 | 7 (0) | 4130.1 s = 68.8 min | 114.6 |
| Dragon net escape | 48.708 s | 10 | 10 (0) | 6034.4 s = 100.6 min | 123.9 |
| **All three** | 114.750 s | 23 | 23 (0) | 13698.4 s = 3.81 h (228.3 min) | 119.4 |

## Per shot
- One 5.167 s, 1280x704 clip with audio at 16 steps took 585.8 to 611.2 s (mean 595.6 s = 9.9 min) over 23 shots.
- Timeline for every shot: PROMPT-PACK.md and prompt-pack.json.

## Time to make a 45 s and a 1 min clip (derived)
- **Measured rate:** 13698.4 GPU s for 114.750 s of finished film = **119.4 GPU s per finished second**.
  - 45 s = **90 min** of GPU time.
  - 1 min = **119 min** of GPU time.
- **Measured closest case:** the 48.7 s Dragon net escape took **100.6 min** (10 shots, 0 retries).
- **Check by shot count:** each shot adds about 5.125 s of film after the chained-frame trim.
  - 45 s needs 9 shots × 595.6 s = 89 min.
  - 60 s needs 12 shots × 595.6 s = 119 min.
- These figures assume no retries. This run had none; a run that needs retakes costs one shot time per retake.

## Wall clock
The first prompt started at 2026-10-29 01:44:50.250 CDT and the last one ended at 2026-10-29 05:34:23.684 CDT, 229.6 min in all for the three scenes. Of that, 228.3 min was GPU execution. The rest is the gaps between prompts, chiefly 74 s before D10.

## Not covered (cannot be proven from these receipts)
- **Reference stills.** 14 of the 23 reference images are stills. Their generator and generation time are not in the ComfyUI graph or history, so the GPU totals above leave them out. The other 9 are the previous shot's last frame (chained continuity: F02, F04, E03, E04, E06, E07, D06, D08, D10), which needs no extra GPU work.
- **Editing time.** The assembly of the production finals (cuts, sound) is not timed here.
- **Other GPU jobs.** We cannot prove the GPU was idle apart from this queue. ComfyUI :8196 on the same box logged no jobs on 2026-10-29, but other processes were not checked.
- **Keel acceleration.** These shots used the stock H3 graph at 16 steps. Keel's FirstBlockCache, Motion-Context and the 4-step turbo were not in the graph. Keel's 3.16x and 1.44x speed-ups do NOT apply to these timings, and the films do not claim them.
- **Model load.** We cannot say whether the model was reloaded between prompts. Every prompt reports `execution_cached`, meaning the loader nodes were cached, so the load was most likely paid once, before F01. F01 (595.9 s) is within 10 s of the other forest shots. That rules out a reload on the scale of Keel's ~232 s model load inside these timings.
