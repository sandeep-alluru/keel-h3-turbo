# Published comparisons — NVIDIA Sol-Engine and ComfyUI-Sol-H3

Every number in this file is **PUBLISHED**: measured by somebody else, and quoted here with the
source it came from and the sentence it came from. Nothing here is a measurement we took.

This is the receipt behind the baseline comparison table on the front page. It exists so that the
table's rows can be checked without leaving the repository.

---

## 1. NVIDIA Sol-Engine — `NVlabs/Sana` @ `sol-engine`

### The speedups table

`models/minimax_h3/README.md`, section "Performance":

| Hardware | GPUs | Workload | Baseline (s) | Optimized (s) | Speedup | Config |
|---|---:|---:|---:|---:|---:|---|
| GB200 | 8 | 768p@5s | 27.21 | 6.88 | **3.95x** | `config/minimax_h3/fullopt.toml` |
| GB10 (DGX Spark) | 1 | 480p@5s | 710.6 | 181.3 | **3.92x** | `config/minimax_h3/gb10_fullopt.toml` |
| RTX 4090 | 1 | 768p@5s | 2239.22 | 504.33 | **4.44x** | `config/minimax_h3/rtx4090_fullopt.toml` |
| RTX 5090 | 1 | 768p@5s | 1045.4 | 231.2 | **4.52x** | `config/minimax_h3/rtx5090_fullopt.toml` |
| H100 | 4 | 768p@5s | 81.47 | 22.89 | **3.56x** | `config/minimax_h3/h100_fullopt.toml` |
| A100 | 4 | 768p@5s | 217.32 | 61.28 | **3.55x** | `config/minimax_h3/a100_fullopt.toml` |

The table's own footnote:

> *"Speedups are measured against the matching baseline runtime on the same hardware. Each platform
> uses its validated release workload, so the table compares relative acceleration rather than
> absolute latency across GPUs."*

**Keel's row uses the GB10 line: 710.6 s → 181.3 s, 3.92×.** The workload is 480p@5s; the
per-GPU config `config/minimax_h3/gb10_fullopt.toml` gives the geometry as **832×480, 124 frames,
50 steps**.

### The GB10 baseline, and what it is made of

`config/minimax_h3/gb10_baseline.toml`, `description`:

> *"MiniMax-H3 on one GB10 with no acceleration: pruned FP8 checkpoint read into upstream Modular
> Diffusers, eager quantiser, no fused kernels, no cache, no sparse attention. The FP8 weights are
> the substitution that makes the model fit at all, not an optimisation — measured at 13,428 ms/step
> against the released BF16 model's 13,417 ms, a 0.08% difference."*

and the baseline config's `summary`:

> *"The denominator for every row below. It is not the GB200 baseline and is not comparable to
> it: different hardware, different checkpoint, a tenth of the canvas."*

Two things Keel quotes from this:

* **13,428 ms/step** against the BF16 model's **13,417 ms/step** — a **0.08 %** difference. FP8 is
  not a speed trick; it is the substitution that makes the model resident, at no measurable step
  cost. That is NVIDIA's measurement, not ours.
* NVIDIA are careful about the same thing Keel is careful about: their baseline is *their* baseline
  and never transfers to another hardware or another checkpoint.

Source: <https://github.com/NVlabs/Sana/tree/sol-engine>

---

## 2. ComfyUI-Sol-H3 — `xmarre/ComfyUI-Sol-H3`

### The matched SOL A/B

From their README, section "Default: one dense trajectory evaluation", quoting their own metrics:

| Run | SOL | `dense_evaluations` | Logical | Actual | Forecast | H3 sampler | End-to-end |
|---|---|---:|---:|---:|---:|---:|---:|
| `metrics_00321` | on | 1 | 40 | 26 | 14 | 353.36 s | 400.94 s |
| `metrics_00322` | off | — | 40 | 25 | 15 | 374.84 s | 420.81 s |
| `metrics_00323` | on | **0** | **40** | **25** | **15** | **332.56 s** | **380.57 s** |

Their own reading of it:

> *"In this controlled hot pair, SOL reduced H3 sampler wall by 42.28 s (11.3%) and end-to-end wall
> by 40.24 s (9.6%). Arithmetic-gate and general hot-run variance still exist, so this remains
> deployment-specific evidence rather than a universal percentage."*

**Keel's two xmarre rows are these two:**

* SOL on at the current default (`dense_evaluations=1`): 420.81 s → **400.94 s**, **1.05×**.
* SOL on in the speed mode (`dense_evaluations=0`): 420.81 s → **380.57 s**, **1.11×**.

Their default was reverted to `dense_evaluations=1` after a controlled same-seed comparison found
a quality regression:

> *"With `dense_evaluations=0`, the opening motion showed an abrupt pose/orientation change with
> heavy early smearing before settling into the opposite heading. With `dense_evaluations=1`, the
> corresponding opening motion remained a continuous turn."*

and:

> *"The pair establishes that SOL-first execution **can** destabilize the initial trajectory. It
> says nothing about how frequently this occurs across seeds, prompts, references, resolutions or
> model variants."*

**That is why Keel publishes the speed mode separately from the default.** A 1.11× that comes with
a documented trajectory destabilisation is a different claim from a 1.05× that carries no
documented destabilisation, and presenting only the faster one would misrepresent it.

### Hardware and geometry

Their production validation ran on:

> *"an **NVIDIA RTX PRO 6000 Blackwell Workstation Edition (SM120)** with PyTorch `2.10.0+cu130`"*

SM121 / GB10 support landed in v0.1.7, and they say plainly where that claim stops:

> *"This support claims no independent maintainer GB10 benchmark or SM120/SM121 performance
> equivalence."*

**Their published timings do not state a resolution or a step count.** Their README and their
`docs/VALIDATION.md` give the call topology (logical / actual / forecast NFE counts) but no
geometry. Keel's baseline table therefore leaves the geometry and step columns blank for their
rows rather than guessing them, and their rows are the only ones in the table that are not on a
DGX Spark.

### Also worth naming, because Keel uses it

Their Exact Runtime A/B, from their README:

| Exact Runtime | Sampler | End-to-end | Peak VRAM |
|---|---:|---:|---:|
| off | 263.56 s | 312.57 s | 17.18 GB |
| on | **247.30 s** | **298.69 s** | 17.18 GB |

> *"This is Exact-only evidence, not a SOL speed claim."*

Keel neither reproduces nor contests these; they are recorded here because the numbers are public
and because Keel's own discipline — a matched A/B with the control stated explicitly — was written
in the light of how they publish theirs.

Source: <https://github.com/xmarre/ComfyUI-Sol-H3>

---

## 3. The community Sol-Engine port for a single DGX Spark

Covered separately, because it is the one this repository reproduces most often:
`receipts/bench-results.md` carries the published ladder verbatim with a provenance header, and
`receipts/PROVENANCE.md` maps every row of it.

---

## What Keel never claims from any of these

* Keel makes no claim to NVIDIA's 3.92×. It was measured on NVIDIA's runtime, with NVIDIA's kernels,
  at 832×480 and 50 steps.
* Keel makes no claim to the community port's 1.54×. It was measured on `spark-13b3`, in that
  author's repository, and Keel reproduces it with attribution.
* Keel makes no claim to xmarre's 1.05× or 1.11×. They were measured on SM120 with a different call
  topology, at an unstated geometry.
* Keel never compares its own 1.44× against any of them as though the geometries matched. They
  never match. The front-page table is deliberately unblended so that a reader can see that for
  themselves.
