# Three scenes, 2026-10-29: GPU-time receipt

Source of record: `production/three-scenes-2026-10-29/` (BENCHMARKS.md, PROMPT-PACK.md, prompt-pack.json and receipts/). GPU time per shot = ComfyUI `execution_success - execution_start` from the spark2 `/history` (filtered to these 23 prompts, `production/three-scenes-2026-10-29/receipts/spark2-8188-history.json`). Queue wait excluded.

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

