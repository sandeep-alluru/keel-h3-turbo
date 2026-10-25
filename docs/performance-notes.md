# Performance notes

Four things that will cost you a day if you don't know them. Each one was measured on a DGX Spark
and each one is filed in `receipts/`.

## 1 — `torch flex_attention` is wrong on Blackwell

It compiles, it runs, and it raises nothing. Cosine similarity against dense SDPA is **0.9167 at
S=1536** and **0.9688 at S=4096**. The error compounds across 50 blocks × 20 steps into visible
noise. The working alternatives measure 0.99995–0.99998.

Do not reach for `flex_attention` on `sm_121`.

## 2 — a download can be broken and still look right

Twice on this project, and both times the file had the right name.

The text encoder arrived at 21,714,795,671 bytes with a header declaring the right length and
6,027,653,120 bytes of garbage behind it. It loads. It produces nothing. It raises nothing.

The BF16 DiT arrived at 35,660,245,251 bytes with a header declaring **66,280,487,368**. It is
30,620,242,117 bytes short and will not load at all. That truncated file's size is where this
repository's old "35.7 GB BF16" claim came from — it was `ls -l` output read as a model size.

**Quote a checkpoint size from the safetensors header, never from `stat`.** The header is what
the file promises to be; the size on disk is only what survived the download.
`receipts/encoder-diagnosis.md` and `receipts/checkpoint-sizes.md` have both cases and the check.

## 3 — FirstBlockCache's step curve is U-shaped, not monotone

The per-row diff ratio falls from .179 at step 1 to a minimum around step 10 and climbs back to
.249 by step 19. With the guards (`start_step=3`, `end_dense_steps=2`,
`max_consecutive_skips=2`) it skips 6 of 20 steps — 6, 7, 9, 10, 12, 13 — but the tail is where it
gets expensive again.

Set the guard from the curve, not from a gut feel.

## 4 — two Sparks over Ethernet is slower than one Spark

Context parallelism across two nodes runs at 5.52 GB/s over fabric against 503 GB/s over NVLink.
Splitting the render across two machines loses far more than the parallelism wins.

This is why the whole stack here is designed to run on one box.
