# Our own acceleration A/B — the first-party number

This is the only first-party performance comparison in this repository. It is here because a
repository that publishes someone else's ladder and calls it ours would be lying, and because the
gap between the two is the most interesting thing on the page.

## What was measured

The team ran the acceleration stack on its own DGX Spark and compared it against its own
unaccelerated baseline, at production resolution.

| | s/step | Run |
|---|---:|---|
| Baseline, Sage + FirstBlockCache **combined** | 39.8 | 10 m 37 s for 16 steps |
| Accelerated, Sage + FirstBlockCache combined | 34.1 | 9 m 05 s for 16 steps |
| **Measured gain** | **1.17×** | ~14 % faster |

And, with the two isolated at 704×1280:

| | Wall |
|---|---:|
| Arm B1 | 347 s |
| Arm B4 | 344 s |
| **Measured gain** | **~1.0× — no meaningful difference** |

FirstBlockCache on its own came out at **~0×**. The batched VAE decode node **was never enabled
at all** in any of these runs.

The team's own conclusion, recorded in the session at the time:

> *"Honest result: 34.1 vs 39.8 s/step = 1.17×. Not the 1.4-2× claimed."*

and later, when the community port's five claims were checked against what had actually been
measured here:

> *"We got 1.17× from Sage + FirstBlockCache, and ~1.0× when we isolated them at 704×1280
> (B1 347 s vs B4 344 s) … FirstBlockCache: ~0×. We never enabled the batched VAE decode node at
> all … we validated almost none of it … the Sol-Attn stack remains unproven here, not
> disproven."*

## Where this comes from

These are readings from the team's own DeepSeek session on the local Spark, quoted from the
session record. They are first-party in the sense that this team ran them — but they were not
written up as a formal receipt at the time, which is exactly why this file exists now.

For the Spillway-level Sage test specifically, `receipts/sage-attention-ab.md` is the primary
record, and it is worth reading alongside this one: at the keeper's own geometry and seed, the
Sage node **rejected Sage compatibility before sampling** (node 20), so no speedup or quality
equivalence was claimed from that arm at all. The 1.17× above is the earlier, completed
comparison at the wider production resolution. The two are not the same experiment and they do not
contradict each other — they are two different attempts, one of which completed and one of which
did not get as far as sampling.

## How this compares to the published ladder

| | Published ladder | Our own A/B |
|---|---|---|
| Who measured it | The community Sol-Engine port's author | This team |
| Host | `spark-13b3` | our Spark |
| Geometry | 864×480, 124 frames, 20 steps | 704×1280 / 768×1344, 124 frames, 16 steps |
| Control | 312.7 s end-to-end, 14.40 s/step | 39.8 s/step |
| Full stack | 202.5 s end-to-end, 8.39 s/step | 34.1 s/step |
| Ratio | 1.54× end-to-end, 1.72× per step | **1.17×** |
| Batched VAE decode | included | never enabled |
| Sol-Attn | included | never installed here |

Two things follow, and both matter:

1. **These are not the same workload.** Different resolution, different step count, different
   machines. The 1.17× does not "contradict" the 1.54× and the 1.54× does not "confirm" the
   1.17×. They are two separate experiments and the honest statement is that the larger speedup
   has not been reproduced on our hardware.
2. **The comparison is not fair to either side.** The published ladder includes Sol-Attn and the
   batched VAE decode; our run included neither. The Sol-Attn stack was left *unproven here, not
   disproven* — but it was not proven either.

## What this receipt does not say

It does not say the acceleration stack does not work. It says that on our box, with the
configuration we had actually wired up, the gain was 1.17× combined and roughly nothing isolated,
and that we never installed the Sol-Attn kernel that the published ladder depends on.

Re-running the published ladder on our own hardware would turn this file into a first-party
comparison of the whole stack. `RECIPE.md` is written for exactly that run.
