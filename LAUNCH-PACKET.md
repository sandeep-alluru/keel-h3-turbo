# LAUNCH PACKET — internal

> **This file is internal.** It is committed to the repository, which is **private**. It is not
> part of the public README and it should be removed or rewritten before any public flip.
> Every owner decision below is listed as a decision, not as a recommendation.

**Product (PROPOSED):** **Keel** — *accelerated MiniMax H3 video diffusion inference on a single
DGX Spark*
**Technique (PROPOSED):** **Trim** — fit the model to the machine, cut the steps, then measure
the cut
**Repository:** `sandeep-alluru/minimax-h3-local-engine` — **private**
**Prepared:** 2026-10-25 · **Working copy:** `/home/clawerdigi2/AgentHub/model-acceleration/minimax-h3-local-engine`
**Push route:** `samurai1` → `clawer-samurai-1@100.90.129.41:/home/clawer-samurai-1/AgentHub/release-staging/minimax-h3-local-engine` (verified working; `gh` authenticated as `sandeep-alluru`)

---

## 1a. Product identity — PROPOSED, for the owner to approve

The owner's review was that the repository read like an agent finishing a task rather than a
product being launched: no product title, no headline, no product direction, and a README that
opened with a description of a folder.

This rework proposes the following. **Every name here is the owner's to approve.** Nothing ships
under a name the owner has not chosen.

| | Proposed | Notes |
|---|---|---|
| **Product title** | **Keel** | A short, ownable, developer-readable name. One word, so `git clone keel`, `pip install keel` and "I run Keel" all work. |
| **Headline** | *Accelerated MiniMax H3 video diffusion inference on a single DGX Spark.* | Plain gerund phrase, in the same register as NVIDIA's "accelerated video diffusion inference". |
| **Description** | *An efficiency-oriented inference stack for MiniMax H3 — installable ComfyUI node packs, a resident-weight recipe, and a receipt behind every number.* | Mirrors the shape of NVIDIA's own one-line description. |
| **Named technique** | **Trim** | NVIDIA's name is Sol-Attn. Ours covers the choices that make one machine enough plus the method of proving they work: **Trim**-Residency, Trim-INT8, Trim-NVFP4, Trim-Step, Trim-A/B, Trim-Receipts. |
| **Alternate product name** | *Trim* | If the owner prefers one name rather than two, promoting the technique to the product title is a one-line change. |
| **Repository name** | `minimax-h3-local-engine` → `keel` | **Not changed.** Renaming the GitHub repository is the owner's call and it changes the public URL. The README's repo layout tree shows `keel/` as the proposed directory name. |

**The direction, stated in the first screen of the README** — what it is, what it is not, and
where it is going:

* **is** — a way to run MiniMax H3 on one DGX Spark, for people who want to render H3 themselves
  rather than call an API: node packs, the weight set that fits in unified memory, a seed-matched
  A/B method, and a checker that fails the build when a number loses its receipt.
* **is not** — NVIDIA's Sol-Engine, and not trying to be. `Sol-Attn` is NVIDIA's name for their
  method; the published ladder belongs to the community port and says so wherever it appears.
* **is going** — in one direction, and it is not a new kernel. The published ladder reaches 1.54×
  using two components this team has never installed. Closing that gap is the next run, and
  `RECIPE.md` is written for it.

### The baseline comparison table

This is the table the owner asked for, and it is now the second thing on the front page. Every row
is labelled PUBLISHED (with the repository it came from) or FIRST-PARTY (with the receipt here).
The two are never blended, and the geometries differ, so the table is deliberately unblended.

| Engine | Hardware | Geometry | Steps | Seconds | Speedup | Source |
|---|---|---|---:|---|---:|---|
| **Stock MiniMax H3** — no acceleration | DGX Spark, GB10 | 832×480, 124f | 50 | 710.6 s | 1.00× | PUBLISHED · NVlabs/Sana `sol-engine` |
| **NVlabs Sana Sol-Engine** — full opt | DGX Spark, GB10 | 832×480, 124f | 50 | **181.3 s** | **3.92×** | PUBLISHED · NVlabs/Sana `sol-engine` |
| **Stock ComfyUI** — no acceleration | DGX Spark, `spark-13b3` | 864×480, 124f | 20 | 312.7 s | 1.00× | PUBLISHED · community SM121 port |
| **Community Sol-Engine port** — full stack | DGX Spark, `spark-13b3` | 864×480, 124f | 20 | **202.5 s** | **1.54×** | PUBLISHED · community SM121 port |
| **ComfyUI-Sol-H3 (xmarre)** — SOL on, default | RTX PRO 6000, SM120 | not stated | not stated | 420.81 → **400.94 s** | 1.05× | PUBLISHED · xmarre/ComfyUI-Sol-H3 |
| **ComfyUI-Sol-H3 (xmarre)** — SOL on, speed mode | RTX PRO 6000, SM120 | not stated | not stated | 420.81 → **380.57 s** | 1.11× | PUBLISHED · xmarre/ComfyUI-Sol-H3 |
| **Keel** — acceleration vs plain control | DGX Spark, GB10 | 1280×704, 124f | 8 | 496 → **344 s** | **1.44×** | **FIRST-PARTY** · `receipts/bench-matrix.tsv` |
| **Keel** — acceleration vs plain control | DGX Spark, GB10 | 1280×704, 124f | 16 | 635 → **545 s** | **1.17×** | **FIRST-PARTY** · `receipts/bench-matrix.tsv` |
| **Keel** — 4-step turbo LoRA | DGX Spark, GB10 | 1280×704, 124f | 4 | **201 s** | **3.16×** | **FIRST-PARTY** · `receipts/bench-matrix.tsv` |

Three observations the owner should have before the flip:

1. **NVIDIA's 3.92× is the strongest number in the table and it is theirs.** Any comparison that
   implies otherwise would be dishonest, and the README says so in the first screen.
2. **The community port's 1.54× is the strongest number for a ComfyUI node-pack stack on one
   Spark.** Keel reproduces it with attribution rather than claiming it. It is also the number
   Keel's own 1.44× is *not* comparable to — different geometry, different step count, different
   machine.
3. **xmarre's rows are the careful ones.** They publish a matched A/B, they publish the speed mode
   separately from the default because the speed mode has a documented trajectory destabilisation,
   and they do not publish the geometry for their timings. Keel leaves that column blank rather
   than guess it.

Receipt for every published number in this table, with the quoted sentences:
`receipts/published-comparisons.md`.

### The named technique stack

| Technique | What it does | Weights it touches | Measured effect |
|---|---|---|---|
| **Trim-Residency** | Pruned FP8 DiT + NVFP4/AWQ encoder so the whole model fits in 121 GB of unified memory | FP8 DiT 20.96 GB, NVFP4 encoder 15.69 GB | 42.46 GB total vs 123.60 GB for the BF16 pair — the difference between running and not running. FP8's step cost: **0.08 %** (13,428 vs 13,417 ms/step) — *PUBLISHED, NVIDIA* |
| **Trim-INT8** | The convert path for machines with more room | INT8 ConvRot DiTs 34.04 GB, pruned INT8 Convrot 20.97 GB | **No speed measurement of its own** — a residency choice, not an acceleration. Stated plainly |
| **Trim-NVFP4** | The INT4 conditioner, and the download discipline that goes with it | NVFP4/AWQ encoder 15.69 GB | Caught a 21,714,795,671 B encoder with 6,027,653,120 B of trailing garbage, and a truncated BF16 DiT 30.6 GB short of its own header |
| **Trim-Step** | Step distillation: 4-step and 8-step turbo LoRAs instead of 20 steps | turbo LoRAs, 1.96 GB each | **201 s** against the 635 s 16-step plain baseline — **3.16×** |
| **Trim-A/B** | Control and treatment differ only in the acceleration — same seed, geometry, steps, scheduler | none | **1.44×** at 8 steps, **1.17×** at 16 steps |
| **Trim-Receipts** | Every published number maps to who measured it; the build fails when one stops matching | none | Not a speed effect. It is why the other five rows can be trusted |

**Not claimed:** per-technique speedups where none were isolated. Trim-INT8 has no number of its
own, and Trim-A/B cannot separate Sage attention from FirstBlockCache, because the surviving
records do not resolve which of the two produced the gain.

## 1. Current state

### What the repository is now

A **private** repository that packages MiniMax H3 model acceleration for a single NVIDIA DGX Spark
(GB10, `sm_121`), with the measurement discipline attached.

**Product identity (PROPOSED):** **Keel** — *accelerated MiniMax H3 video diffusion inference on
a single DGX Spark*. **Named technique (PROPOSED):** **Trim**. Both are the owner's to approve;
see §1a and §5.

| | |
|---|---|
| Commits before this pass | 2 (`565b6c2`, `428a4e5`), both 2026-10-25, both packaging — no measurement |
| Commits after this pass | see `git log --oneline` |
| Front page | rewritten: origin story, results, provenance, install, failure modes, credits |
| Receipts | 12 files, including a new `PROVENANCE.md` index |
| Curated clips | 6, hash-verified, enforced by `scripts/check_receipts.py` |
| CI | `.github/workflows/claims.yml` runs the checker on every push |
| Charts | `charts/end-to-end.png`, `charts/per-step.png`, generated **from** the receipt |
| Release | `v0.1.0` draft, 6 assets attached — body updated this pass |
| Licence | **not addressed anywhere.** Deferred by the owner, per instruction |

### The single most important thing to understand about this repository

**Almost every headline number in it was measured by somebody else.** The speed ladder
(312.7 s → 202.5 s, 1.54× end-to-end, 14.40 → 8.39 s/step, 1.72×) is the published benchmark of
the community Sol-Engine port for a single DGX Spark, measured on host `spark-13b3`.

The previous revision of this repository presented those numbers as its own receipts, with the
host line rewritten from `spark-13b3` to `gb10-spark`. That has been corrected: the host is
restored, the upstream repository and commit are named, and the file carries a provenance header.
The same is now true of the three vendored node packs, which are unmodified upstream trees.

What this team actually measured, and can be held to:

| | |
|---|---|
| Pruned FP8 DiT, byte-exact + hashed | 20,958,205,608 B, SHA-256 `12944c1f…` — matches the published hash exactly |
| NVFP4/AWQ encoder, clean re-download | 15,687,142,551 B |
| The corrupt first encoder | 21,714,795,671 B, 6,027,653,120 unaccounted trailing bytes |
| A real H3 forward pass + video and audio decode | 30.02 s at 512×288, 124 frames, 2 steps |
| Acceleration arms vs plain control, 8 steps, 1280×704 | **1.44×** (496 s → 344 s) |
| Acceleration arms vs plain control, 16 steps, 1280×704 | **1.17×** (635 s → 545 s; 39.8 → 34.1 s/step) |
| 4-step turbo LoRA vs the 16-step plain baseline | **3.16×** (201 s) |
| Three keeper renders | 710.15 s / 710.13 s / 710.14 s |
| Every published checkpoint size | byte-exact, in `receipts/checkpoint-sizes.md` |
| Turbo LoRA sizes and SHA-256 | verified directly on the weights tree, in `receipts/adapter-shelf.md` |

**This is the honest position and it is a defensible one**: the acceleration *stack* is
third-party and the *published speed ladder* is third-party, but the first-party A/B, the
residency work, the corruption diagnosis, the production harness, the craft gates, the curation,
and the receipts are ours. The repository now says exactly that, everywhere.

**Our own A/B is 1.44× at 8 steps and 1.17× at 16 steps** — lower than the published 1.54×,
because the two components the published ladder depends on (the Sol-Attn kernel and the batched
VAE decode) were never installed in our runs. The largest first-party number we hold is the
**4-step turbo LoRA at 201 s, 3.16×** against the 16-step plain baseline.

### Corrections made this pass

| Was | Now | Why |
|---|---|---|
| `35.7 GB` BF16 DiT → `21.0 GB` FP8 | **66.3 GB** BF16 → 21.0 GB pruned FP8 (34.0 GB INT8 ConvRot) | The BF16 FL2VA/Ref2VA DiTs are 66,280,487,368 B. `35.7 GB` matches no published checkpoint. |
| "3 of 15 shots locked as keepers" | Two owner-locked + one pre-halt agent selection | The halt record names two. |
| Films "30 s, 1080p" | 1920×1056, 31.104 s | Measured with `ffprobe` on the actual release assets. |
| Bench receipt on host `gb10-spark` | Host `spark-13b3`, with provenance header | Upstream's own text. |
| "Node packages ported and packaged by us" | Credits section naming each author | All three are unmodified upstream trees. |
| "One partition is ~135 GiB BF16" | 72.09 GB per partition, 189.88 GB full checkout | Arithmetic on the byte-exact table. |
| "35.7 GB … it fits" | The FP8 pair (42.4 GB) is what fits | 66.3 + 51.5 + 5.81 = 123.6 GB does not fit in 121 GB. |
| Seed 46 vs 45 in the shipped A/B workflows | Both at seed 46, in a root `workflows/` pair | A different seed is not an A/B. Upstream's own bench says "same prompt and seed 46". |
| The isolated A/B quoted as "347 s → 344 s, ~1.0×" | **496 s → 344 s = 1.44×** at 8 steps, and 635 s → 545 s = 1.17× at 16 steps | 347 appears nowhere in `bench_matrix.tsv`; the matrix's B1 is 496 s. The session's prose summary mis-stated the control arm, and every conclusion drawn from it ("FirstBlockCache ~0×") was wrong. The artifact of record wins. |
| The adapter shelf dropped from the README, with a 63-character LoRA hash | Restored, all three adapters' sizes and SHA-256 verified on the weights tree | A 63-hex-character string is not a SHA-256, and `training/TRAINING.md` still linked to the section that had been dropped. |
| The "35.7 GB BF16" claim | 66.3 GB — and the reason is now on file | 35,660,245,251 B is the size of a **truncated download** whose own header declares 66,280,487,368 B. It is 30.6 GB short and cannot load. |
| The Spillway keepers, the Sage arm, and the 347 s figure filed under one receipt | Separated into `keeper-receipt.json`, `sage-attention-ab.md` and `our-acceleration-ab.md` | `sage-attention-ab.md` records the Sage arm **rejected before sampling**, with no speedup claimed. Filing the 347 s figure against it was wrong. |

### Not changed, deliberately

* The **six-clip set**. Final by owner instruction. The record shows a fourth published film
  (`FILM-DRAGON-30s-1080p-v2.mp4`) that is not in the curated set — see §5.
* **No licence section anywhere.** Deferred by the owner.
* **No timeline or changelog.**
* **The vendored trees.** Left byte-identical to upstream so the credits stay true.
* **The published ladder stays on the front page**, labelled as published, with its receipt. It
  is a real benchmark from a real measurement, and it is the best available number for the stack
  this repository ships.

---

## 2. Competitor gap list

### vs NVIDIA Sol-Engine — `NVlabs/Sana` @ `sol-engine` (the official bar)

**Where they are ahead of us**

| | |
|---|---|
| Owns the kernels | Sol-Attention, `cache_line.py`, `vae_shard.py`, `adaln.py` are NVIDIA's, not a port |
| Owns the number | 710.6 s → 181.3 s (**3.92×**) on DGX Spark, 480p/5 s/50 steps — higher than the 1.54× we publish |
| Breadth | Per-GPU runtimes for GB10, GB200, H100, A100, RTX 4090, RTX 5090; `Sol-H3-ComfyUI`; `Sol-H3-Spark`; `HyperFlow`; H3 → LTX-2.5 super-acceleration |
| Supported paths | SGLang, vLLM, Diffusers, ComfyUI |
| Distillation | 4-step T2V / I2V / Ref2VA paths, learned latent upscaler |
| Docs | A documentation site, `AGENTS.md`, `QUICKSTART.md`, CI |
| Release discipline | Config-per-model-per-hardware, news feed, citation file |
| **Product framing** | A named product, a plain headline, a one-line description, and a models-and-speedups table on the first screen |

**Where we are ahead**

| | |
|---|---|
| ComfyUI-first | Installable node packs and a workflow pair, not a per-hardware config tree |
| A receipt for every number | They publish numbers; we file who measured what, and we also file the numbers that came out flat |
| One-box residency work | The exact checkpoint pairs that fit 121 GB unified memory, byte-exact, with the corrupt-download failure documented |
| The craft layer | Motion / aliveness / control / face gates, a prompt cookbook, and the evidence that a 32 %-alive clip was caught before publication |
| The production lane | Pinned harness, stills manifest, shot list, keeper receipts, curation note, and a curated clip set |
| Negative results | The SageAttention A/B and the isolated FBC result are filed in full. Most repos delete those. |
| **Product framing** | A product title, a plain headline, a one-line description, a direction in the first screen, and a baseline comparison table that puts other people's numbers above ours with their names on them |
| **The weights question** | A byte-exact inventory of every published checkpoint with its SHA-256, and the rule that caught a corrupt download and a truncated one: *quote a size from the header, never from `stat`* |

**The gap that matters most:** NVIDIA publishes 3.92×; we publish 1.54× and say whose it is.
A reader who installs NVIDIA's own recipe gets a better number than our front page shows. We
cannot close that without running their path. We can close it *on the ComfyUI path* by running the
ladder ourselves — see §4.

### vs the community Sol-Engine port for a single Spark (the ComfyUI bar)

**Where they are ahead**

| | |
|---|---|
| The published ladder | It is theirs; we reproduce it with attribution |
| The 1.66× batched VAE decode | Their node, their measurement |
| The flex_attention failure analysis | Their finding; we quote it |
| The GB10 spin-wait patch | Their patch, their fleet measurement |
| A standalone installer | `install.sh` stands up the whole stack |

**Where we are ahead**

| | |
|---|---|
| Everything upstream of the bench | The precision work, the corruption diagnosis, the production harness, the gates, the curation, the receipts |
| The A/B workflows | Ours are seed-matched; theirs are not |
| Honesty about attribution | They do not credit NVIDIA's kernels in their README; we credit seven sources |
| The craft layer and the curated set | They have neither |
| A claim checker | `scripts/check_receipts.py` fails the build when a claim loses its receipt |

### vs `xmarre/ComfyUI-Sol-H3`

Their repo integrates "Exact Runtime" optimizations with Sana Sol-Attn, rectangular Q/KV
attention, VDN, Spectrum and untwisted RoPE, and is the closest thing to a ComfyUI-native
alternative.

**They are ahead of us on published evidence, and we now say so in our own table.** Their matched
SOL A/B is 420.81 s → **400.94 s** at the default `dense_evaluations=1` (1.05×) and 420.81 s →
**380.57 s** in the `dense_evaluations=0` speed mode (1.11×), on an RTX PRO 6000 (SM120). Their
numbers are honest in a way we have tried to match: they publish the control, they publish the
sampler wall separately from end-to-end, and they publish the speed mode **separately from the
default** because a controlled same-seed comparison showed SOL-first execution can destabilise
the opening trajectory.

**Where we are ahead:** our baseline table puts their rows in it *by name and by source*, their
hardware is SM120 rather than a Spark, and their published timings do not state a resolution or a
step count — so we leave that column blank rather than guess it. Their Exact Runtime A/B
(312.57 s → 298.69 s) is published too, and is recorded in `receipts/published-comparisons.md`.

They are GPL-3.0. The licence question (deferred) would need to consider them if they were
vendored. They are not.

---

## 3. Readiness checklist

### Content

- [x] README rewritten at the standard of the Sol repos — origin, results, provenance, install, failure modes, stack table with origins, credits
- [x] Every published number traced to a receipt — enforced by `scripts/check_receipts.py`, passing
- [x] `receipts/PROVENANCE.md` — number-by-number map, including the corrections table
- [x] Upstream host restored; upstream repository and commit named on the bench receipt
- [x] Three vendored packs credited, with links
- [x] `35.7 GB` removed; `66.3 GB` / `34.0 GB` / `21.0 GB` substituted, byte-exact
- [x] Keeper lock status corrected (2 owner-locked, 1 pre-halt selection)
- [x] Film geometry corrected to measured values
- [x] A/B workflows seed-matched at the repository root
- [x] Charts generated from the receipt, with the provenance line on the chart itself
- [x] `RECIPE.md` rewritten as our own agent-executable procedure
- [x] Deployment guide arithmetic corrected
- [x] Six-clip set final and hash-verified
- [x] `LAUNCH-PACKET.md` written (this file)

### Product rework (owner review, 2026-10-25)

- [x] Product title, plain headline and one-line description — **PROPOSED** in §1a, the owner's to approve
- [x] Product direction in the first screen: what it is, what it is not, where it is going
- [x] Baseline comparison table up front — engine, hardware, geometry, steps, seconds, speedup, source, every row PUBLISHED or FIRST-PARTY
- [x] Our own technique named, **PROPOSED**, and documented technique by technique with receipts
- [x] Weights section: every weight with source, size, SHA-256 and what we did to it; the publish-weights option laid out as an owner decision
- [x] "What we did" rewritten in plain language for a developer who has never seen this fleet
- [x] All honesty corrections from the previous pass kept — provenance, attribution, the corrected numbers
- [x] Demo re-produced against the new front page
- [x] Four owner decisions presented as decisions, not prose: product name, technique name, weights publishing, public flip

### Mechanics

- [x] `scripts/check_receipts.py` — stdlib only, passes locally
- [x] `.github/workflows/claims.yml` — runs the checker on every push and PR
- [x] Charts generator committed alongside the charts
- [x] Commits pushed via the `samurai1` route
- [x] Draft release `v0.1.0` body updated to match the corrected repository
- [x] Demo video produced and listed in §6

### Not done, and why

- [ ] **No first-party ladder.** The published ladder was not re-run on our hardware. This is the
      single biggest gap in the repository and the only one that would change the front page.
- [ ] **No licence determination.** Deferred by the owner. The repository contains three vendored
      trees (Apache-2.0, MIT and GPL-3.0 respectively) and ships no model weights.
- [ ] **No public flip.** Owner's decision alone.
- [ ] **No tag.** `v0.1.0` exists as a draft release; there is no git tag.
- [ ] **No raw bench logs.** There is no first-party log to publish; the published ladder's raw
      logs live upstream and we reproduce their published file.

---

## 3b. Operational hazards found on the other Spark (`spark-8cf2`)

Found while mining the fleet. **Nothing in this repository is affected, and nothing was changed on
that box** — but the owner should know, because both items are live.

1. **The corrupt text encoder is still installed there.** The 21,714,795,671-byte copy — the one
   with 6,027,653,120 bytes of trailing garbage — is still in that ComfyUI's `models/text_encoders/`
   and is still what its live `CLIPLoader` resolves. The clean 15,687,142,551-byte encoder lives
   at a different path under `production/video/mara/a025/checkpoints/Comfy-MiniMax-H3/`. **The
   encoder fix is not wired into that box.**
2. **A truncated BF16 DiT is still there**, at 35,660,245,251 bytes against a header that declares
   66,280,487,368. Nothing on that box can load it. It should be deleted or re-downloaded.
3. That box also has the H3 **node packs absent** — its `custom_nodes/` holds only
   `comfyui-krea2edit` and `KJNodes`, and ComfyUI itself ships native H3 support. So the
   acceleration stack has never been installed there, which is consistent with the ladder
   receipts living elsewhere.
4. Its live ComfyUI was **holding 40,611 MiB with another CUDA process active** while we looked.
   Any timing taken on that box under those conditions is not comparable to anything.

## 4. What remains

### 4a. The first-party ladder — the one thing that would change the front page

Run the corrected `workflows/` pair on a Spark and file the result as a first-party receipt.

* **Cost:** one GPU session, roughly 10–12 minutes of render plus setup.
* **Prerequisites:** a Spark with the FP8 or INT8 ConvRot DiT and the NVFP4 encoder already
  downloaded, ComfyUI up, the three node packs installed, GPU idle.
* **Where the weights are:** the launch lane's local Spark has the encoder at
  `~/.local/share/film-lane-b/models/`; the DiT and VAEs are the missing pieces. The local box
  does not currently have a ComfyUI tree with H3 weights installed.
* **What is already known:** our own matrix gives 1.44× at 8 steps and 1.17× at 16 steps at
  1280×704, and the turbo LoRA gives 3.16× at 4 steps — see `receipts/bench-matrix.tsv`. What the
  run would add is the two components our runs never installed: the **Sol-Attn kernel** and the
  **batched VAE decode**. Until they are in, our number and the published ladder are not
  comparable.
* **Blocker to check first:** the Spillway production is halted. A benchmark render in the
  acceleration lane is not film production, but **do not run anything that touches the Spillway
  lane, the halt, or the keeper receipts.** The owner lifts the halt; nothing here does.
* **Procedure:** `RECIPE.md` §3 and §4.
* **If it comes out slower than published,** that is a legitimate result and it stays. It goes in
  the table as ours, next to theirs.

### 4b. The demo video

Produced this pass and listed in §6. It is a launch asset in the working directory, **not
uploaded anywhere**.

### 4c. Housekeeping

* Tag `v0.1.0` when the release is published rather than drafted.
* Decide whether `LAUNCH-PACKET.md` stays in the repository at the public flip (§5).
* The `receipts/text-encoder-load.log` is a raw log from the corrupt download; consider whether it
  belongs in a public repo or should stay in the internal tree.

---

## 5. Decisions that are the owner's alone

**Four decisions. Each is presented as a decision, not a recommendation buried in prose.**

### Decision 1 — the product name

| | |
|---|---|
| **Question** | Does the project ship as **Keel**, and under what repository name? |
| **Proposed** | Product title **Keel**; headline *accelerated MiniMax H3 video diffusion inference on a single DGX Spark*; description *an efficiency-oriented inference stack for MiniMax H3 — installable ComfyUI node packs, a resident-weight recipe, and a receipt behind every number*. |
| **Alternatives** | Promote the technique name **Trim** to the product title and use one name throughout. Or keep `minimax-h3-local-engine` as the public title, in which case the README's product framing has to be carried entirely by the headline. |
| **What it costs to change** | The name appears in the README title, headline, the repo layout tree, the technique table, `LAUNCH-PACKET.md` and the demo video title card. Nothing structural depends on it. |
| **Also implied** | The GitHub repository is still named `minimax-h3-local-engine`. **Not renamed** — it changes the public URL, so it is the owner's call. |

### Decision 2 — the technique name

| | |
|---|---|
| **Question** | Does the stack ship under the name **Trim**? |
| **Proposed** | **Trim** — *fit the model to the machine, cut the steps, then measure the cut* — with six sub-techniques: Trim-Residency, Trim-INT8, Trim-NVFP4, Trim-Step, Trim-A/B, Trim-Receipts. |
| **Why not something else** | `Sol-Attn` is NVIDIA's name for their method and their word. Ours covers choices (which weights, how many steps) and method (how you measure), so it wants a verb rather than a kernel name. **Trim** is a plain English word that survives being said out loud to another developer, which `Sol-Attn` does not. |
| **Alternative** | If the owner prefers the technique and the product to share a name, **Trim** can be the product title and the technique becomes simply "the Trim stack". |
| **What it costs to change** | Names only. The technique table, the six sub-names, the README, the packet and the demo card. |

### Decision 3 — publishing weights

| | |
|---|---|
| **Question** | Does Keel ever host and publish the weights it uses? |
| **Status** | **Keel publishes no weights today, and this repository contains none.** Nothing in the project does this by default. |
| **What it would take** | ~20.96 GB for the pruned FP8 DiT, ~15.69 GB for the NVFP4 encoder, ~5.82 GB for both VAEs, ~1.96 GB per turbo LoRA. Mirroring the publisher's files byte-for-byte, or re-emitting them, plus somewhere to host them, plus a way to keep the hash table truthful if the mirror diverges from the publisher's copy. |
| **For** | The corrupt-download failure was real and cost a render. A controlled host removes that failure mode. |
| **Against** | These files are already published by the model repository. Re-hosting published weights duplicates a large artefact for no accuracy gain, and it is a redistribution decision rather than a technical one. |
| **Detail** | `receipts/weights.md` |
| **What this repository does today** | Publishes the recipes, the byte-exact table, the published SHA-256s and the hash-check procedure — and no weights. |

### Decision 4 — the public flip

| | |
|---|---|
| **Question** | Does the repository go public, and does `v0.1.0` get published? |
| **Status** | **Not taken.** The repository is private, the release is a draft, and nothing has been uploaded or published. |
| **What is ready** | Everything else in this packet is arranged so that the flip is a single decision with nothing left to prepare: the front page is rewritten to product standard, every published number has a receipt and a label, the claim checker passes in CI, and the release body matches the corrected repository. |
| **What the flip would expose** | That the headline speed ladder is published rather than ours. The README says so in the first screen, and the baseline table puts NVIDIA's 3.92× and the community port's 1.54× above our own 1.44× — visibly, on purpose. That is the honest version of this repository. |
| **Also the owner's** | Whether `LAUNCH-PACKET.md` ships with it. **Recommendation: it does not** — it names gaps and the un-measured ladder. It is a working document. |

### Also open, lower stakes

| # | Decision | Where it stands |
|---|---|---|
| 5 | **The curated set.** | The owner set six and six is what ships. Flagging, not changing: the record shows a fourth published film, `FILM-DRAGON-30s-1080p-v2.mp4` (64.5 % alive, 7.85/16.87 PASS), which is not in the set. If that was deliberate, nothing to do; if it was an oversight, the set becomes seven and `scripts/check_receipts.py` needs its `EXPECTED_FILM_ASSETS` updated in the same commit. |
| 6 | **Whether to publish the ladder as the front page.** | Currently yes, labelled as published and attributed, with NVIDIA's and the community port's numbers above it in the baseline table. |
| 7 | **The asset filenames.** `FILM-WAR-30s-1080p.mp4` is 1920×1056 and 31.104 s. The names are already attached to the draft release and to the clips index. Renaming means re-uploading the assets; leaving them means the names stay slightly wrong. |
| 8 | **The label on the demo video.** | The video now opens with the product title. If the title changes under Decision 1, the video title card changes with it and is rebuilt by `scripts/make_demo.py`. |

## 6. Launch assets

| Asset | Location | Notes |
|---|---|---|
| Draft release `v0.1.0` | GitHub, unpublished | 6 assets attached; body updated this pass |
| Demo video | `/home/clawerdigi2/AgentHub/model-acceleration/MODEL-ACCELERATION-DEMO.mp4` | See §6a |

### 6a. Demo video

| | |
|---|---|
| **File** | `/home/clawerdigi2/AgentHub/model-acceleration/MODEL-ACCELERATION-DEMO.mp4` |
| **Size** | 38,393,423 bytes |
| **SHA-256** | `2ebb2665c4b352f797fa89fa3927f60b886d5d032160f5a6f3fa5eabbb7d6453` |
| **Duration** | **359 s (5 m 59 s)** |
| **Format** | H.264, 1920×1080, 30 fps, 10,770 frames |
| **Rebuild** | `python3 scripts/make_demo.py` in the repository — it re-runs every command it shows and re-reads every receipt, so the video cannot drift from the repo |
| **Published** | **No.** Not uploaded, not linked, not attached to the release. The owner publishes. |

**Coverage, scene by scene (29 scenes, 359 s)**

| # | Scene | What it shows |
|---:|---|---|
| 1 | Card | **KEEL** — the product title, the headline and the one-line description |
| 2 | Card | **The direction** — what it is, what it is not, where it is going |
| 3 | Card | **The baseline comparison table** — every row PUBLISHED or FIRST-PARTY, with NVIDIA's 3.92× and the community port's 1.54× above our own 1.44×, visibly |
| 4 | Card | **The technique: TRIM** — the six sub-techniques, and that the name is the owner's to approve |
| 5 | Card | Two ladders, two owners — 710.6 → 181.3 s (3.92×) and 312.7 → 202.5 s (1.54×), both labelled published |
| 6 | Terminal | `git log`, `git ls-files` — the repository in front of you |
| 7 | Card | **Where it started** — the owner's link to NVIDIA's `sol-engine` branch, the X post, and the community port found the next day |
| 8 | Terminal | The three node packs, listed as they ship |
| 9 | Terminal | The credits — who wrote each part |
| 10 | Terminal | The install — three directories and one installer |
| 11 | Card | **Precision is residency** — 123.60 GB does not fit, 42.46 GB does |
| 12 | Terminal | The real diff between upstream's two workflows, including the seed mismatch (46 vs 45) |
| 13 | Terminal | The seed-matched pair, node by node: same DiT, same encoder, same geometry, same seed, same steps |
| 14 | Chart | End-to-end ladder — 312.7 → 215.7 → 202.5 s, with the provenance line printed on the chart |
| 15 | Chart | Per-step ladder — 14.40 → 8.39 s/step (1.72×), same provenance line |
| 16 | Terminal | **Open the receipt** — `receipts/bench-results.md` and its provenance header |
| 17 | Terminal | `receipts/PROVENANCE.md` — every number and who measured it |
| 18 | Terminal | `receipts/bench-matrix.tsv` — our own first-party benchmark, verbatim |
| 19 | Card | **What we measured ourselves** — the byte-exact sizes, the 30.02 s forward pass, the 1.44× / 1.17× / 3.16× |
| 20 | Card | **The corrupt encoder** — 21,714,795,671 B against 15,687,142,551 B |
| 21 | Terminal | The craft gates — `motion_gate.py` and its calibrated thresholds |
| 22 | Clip | Spillway S01 keeper |
| 23 | Clip | Spillway S02 keeper |
| 24 | Clip | Spillway S03 keeper |
| 25 | Clip | FILM-WAR — finished film |
| 26 | Clip | FILM-BEACON — finished film |
| 27 | Clip | FILM-BRIDGE — finished film |
| 28 | Terminal | `python3 scripts/check_receipts.py` — all five checks green, every claim traced |
| 29 | Card | **KEEL** — the close: the stack, the technique, our own numbers, and the four decisions that are the owner's |

**Every number on screen** is a number that appears in `receipts/`. The published ladder is
labelled as published **on screen**, with the upstream host, in the chart captions and on the
cards, and the baseline table puts NVIDIA's 3.92× and the community port's 1.54× above Keel's own
1.44× — visibly, on purpose.

The video is assembled from real captures — real `git` output, real receipt text, the real charts,
the real clips — and from no generated imagery. `scripts/make_demo.py` re-runs every command it
shows and re-reads every receipt, so the video cannot drift from the repository, and the product
title on the title card follows whatever name the owner approves.

---

## 7. How to verify this packet

```bash
cd /home/clawerdigi2/AgentHub/model-acceleration/minimax-h3-local-engine
python3 scripts/check_receipts.py      # every published claim traced
git log --oneline                      # what changed, and when
git diff 428a4e5..HEAD --stat          # the size of this pass
```

On the staging box:

```bash
ssh clawer-samurai-1@100.90.129.41 \
  'cd ~/AgentHub/release-staging/minimax-h3-local-engine && git log --oneline -5 && python3 scripts/check_receipts.py'
```
