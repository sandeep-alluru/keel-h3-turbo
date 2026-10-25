# Our own acceleration A/B — the first-party numbers

This is the only first-party performance comparison in this repository. It is here because a
repository that publishes someone else's ladder and calls it ours would be lying, and because the
gap between the two is the most interesting thing on the page.

**The artifact of record is `receipts/bench-matrix.tsv`** — 231 bytes, SHA-256
`4df15affc57556e9444faad08655f156c2cbaded585da6ef0fbd1346721bdace`, copied verbatim from the
production tree.

```
config	steps	w	h	accel	wall_s
B1_8s_704_plain	8	704	1280	0	496
B2_16s_480_plain	16	480	832	0	198
B3_8s_480_accel	8	480	832	1	111
B4_8s_704_accel	8	704	1280	1	344
B5_turbo4_704	4	704	1280	lora	201
BASELINE_16s_704	16	704	1280	0	635
```

`w`/`h` are the matrix's own labels; the run log for the matching arm records width 1280,
height 704 — the same frame, landscape.

## What the matrix says

| Comparison | Control | Accelerated | Ratio | Matrix rows |
|---|---:|---:|---:|---|
| **8 steps**, 1280×704, acceleration off vs on | 496 s | **344 s** | **1.44×** | B1 vs B4 |
| **16 steps**, 1280×704, plain baseline vs accelerated | 635 s | **545 s** | **1.17×** | BASELINE_16s_704 + the 16-step accelerated run |
| **4 steps + turbo LoRA**, 1280×704 | 635 s (16-step plain) | **201 s** | **3.16×** | B5 vs BASELINE_16s_704 |

The 16-step comparison is corroborated independently by the per-step figures recorded in the
session: **39.8 s/step plain against 34.1 s/step accelerated**, 10 m 37 s versus 9 m 05 s.
635 / 16 = 39.69 s/step and 545 / 16 = 34.06 s/step — the same two numbers to the decimal.

## Two caveats that change how you read the table

**1. The wall times include the model load.** The run log for the matching arms records
`[h3] loaded in 232.10s on cuda:0`. A load is roughly four minutes of every row, which is why
four steps at 201 s is not simply "half of eight steps at 344 s". These are wall-clock totals for
a complete render, which is the number that matters to somebody waiting for a file — but they are
not sampling-only timings, and they must not be compared against a published table that measures
only the sampler.

**2. The 480×832 pair is not a comparison.** B2 is 16 steps plain at 198 s; B3 is 8 steps
accelerated at 111 s. Different step counts and different wall-clock budget. Any ratio between
them would be meaningless, so none is claimed.

## What was in the accelerated arms

The accelerated arms ran with the acceleration nodes enabled: Sage attention and
FirstBlockCache. **The surviving records do not resolve which of the two produced the gain.** The
session's own assessment at the time was that the Sage patch node may have fallen back silently,
and `receipts/sage-attention-ab.md` records the Sage arm **rejecting Sage compatibility before
sampling** at the shot's own geometry and seed.

So the honest claim is "the acceleration arms as configured". The attribution between Sage and
FirstBlockCache inside those arms is unresolved, and this receipt leaves it unresolved.

**The Sol-Attn kernel was never installed on this box, and the batched VAE decode node was never
enabled in any of these runs.** That is the single biggest difference between this table and the
published ladder, which includes both.

## A correction, because the first version of this file was wrong

An earlier draft of this receipt quoted the isolated A/B as "347 s → 344 s, ~1.0× — no meaningful
difference", taken from the session's own summary line:

> *"We got 1.17× from Sage + FirstBlockCache, and ~1.0× when we isolated them at 704×1280
> (B1 347 s vs B4 344 s) … FirstBlockCache: ~0×."*

**347 appears nowhere in the matrix.** The matrix's B1 is **496 s**. The artifact of
record beats the prose summary, and the summary line appears to have mis-stated the control arm.
Every downstream conclusion in that session — "FirstBlockCache ~0×", "we validated almost none of
it" — was derived from the mis-stated number.

The corrected figures are **1.44×** at 8 steps and **1.17×** at 16 steps, both against a plain
control at the same resolution and step count.

## How this compares to the published ladder

| | Published ladder | Our own A/B |
|---|---|---|
| Who measured it | The community Sol-Engine port's author | We |
| Host | `spark-13b3` | our Spark |
| Geometry | 864×480, 124 frames, 20 steps | 1280×704, 124 frames, 8 and 16 steps |
| Control | 312.7 s end-to-end, 14.40 s/step | 496 s (8 steps) / 635 s (16 steps) |
| Full stack | 202.5 s end-to-end, 8.39 s/step | 344 s (8 steps) / 545 s (16 steps) |
| Ratio | 1.54× end-to-end, 1.72× per step | **1.44×** (8 steps), **1.17×** (16 steps) |
| Includes Sol-Attn | yes | **no** |
| Includes batched VAE decode | yes | **no** |
| Includes the turbo LoRA | no | yes — 4 steps in 201 s, **3.16×** against the 16-step plain baseline |

These are not the same workload, so neither number validates the other. What the table does say
is that **the acceleration arms as configured were worth between 1.17× and 1.44× on our own
hardware**, which is more than the earlier draft of this repository claimed, and that the
published 1.54× has still not been reproduced here because the two pieces it depends on — the
Sol-Attn kernel and the batched VAE decode — were never installed in these runs.

## What this receipt leaves out

It never says the published ladder is wrong. It says our box, our configuration, our
resolution, and our measurement produced 1.17×–1.44×, and that the ladder's extra 1.54× rests on
two components we have yet to run.

`RECIPE.md` is written for the run that would close that gap.
