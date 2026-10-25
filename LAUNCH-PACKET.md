# LAUNCH PACKET — internal

> **This file is internal.** It is committed to the repository, which is **private**. It is not
> part of the public README and it should be removed or rewritten before any public flip.
> Every owner decision below is listed as a decision, not as a recommendation.

**Repository:** `sandeep-alluru/minimax-h3-local-engine` — **private**
**Prepared:** 2026-10-25 · **Working copy:** `/home/clawerdigi2/AgentHub/model-acceleration/minimax-h3-local-engine`
**Push route:** `samurai1` → `clawer-samurai-1@100.90.129.41:/home/clawer-samurai-1/AgentHub/release-staging/minimax-h3-local-engine` (verified working; `gh` authenticated as `sandeep-alluru`)

---

## 1. Current state

### What the repository is now

A **private** repository that packages MiniMax H3 model acceleration for a single NVIDIA DGX Spark
(GB10, `sm_121`), with the measurement discipline attached.

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
| Sage + FirstBlockCache vs baseline | **1.17×** (39.8 → 34.1 s/step) |
| The same two isolated | **~1.0×** (347 s → 344 s) |
| Three keeper renders | 710.15 s / 710.13 s / 710.14 s |
| Every published checkpoint size | byte-exact, in `receipts/checkpoint-sizes.md` |

**This is the honest position and it is a defensible one**: the acceleration *stack* is
third-party and the *speed claim* is third-party, but the residency work, the corruption
diagnosis, the production harness, the craft gates, the curation, and the receipts are ours.
The repository now says exactly that, everywhere.

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

**Where we are ahead**

| | |
|---|---|
| ComfyUI-first | Installable node packs and a workflow pair, not a per-hardware config tree |
| A receipt for every number | They publish numbers; we file who measured what, and we also file the numbers that came out flat |
| One-box residency work | The exact checkpoint pairs that fit 121 GB unified memory, byte-exact, with the corrupt-download failure documented |
| The craft layer | Motion / aliveness / control / face gates, a prompt cookbook, and the evidence that a 32 %-alive clip was caught before publication |
| The production lane | Pinned harness, stills manifest, shot list, keeper receipts, curation note, and a curated clip set |
| Negative results | The SageAttention A/B and the isolated FBC result are filed in full. Most repos delete those. |

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
alternative. We did not benchmark against it, and we do not claim to. It is GPL-3.0, so the
licence question (deferred) would need to consider it if it were vendored. It is not.

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

## 4. What remains

### 4a. The first-party ladder — the one thing that would change the front page

Run the corrected `workflows/` pair on a Spark and file the result as a first-party receipt.

* **Cost:** one GPU session, roughly 10–12 minutes of render plus setup.
* **Prerequisites:** a Spark with the FP8 or INT8 ConvRot DiT and the NVFP4 encoder already
  downloaded, ComfyUI up, the three node packs installed, GPU idle.
* **Where the weights are:** the launch lane's local Spark has the encoder at
  `~/.local/share/film-lane-b/models/`; the DiT and VAEs are the missing pieces. The local box
  does not currently have a ComfyUI tree with H3 weights installed.
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

| # | Decision | Where it stands |
|---|---|---|
| 1 | **The public flip.** Making the repository public. | Not taken. The repository is private and the draft release is unpublished. Everything in this packet is arranged so that the flip is a single decision with nothing else to do first. |
| 2 | **The licence.** | Explicitly deferred. No licence section, no licence analysis, no recommendation appears anywhere in the repository or in this packet. The owner owns this call and it needs to account for the three vendored trees and the model licence before it is taken. |
| 3 | **The curated set.** | The owner set six and six is what ships. Flagging, not changing: the record shows a fourth published film, `FILM-DRAGON-30s-1080p-v2.mp4` (64.5 % alive, 7.85/16.87 PASS), which is not in the set. If that was deliberate, nothing to do; if it was an oversight, the set becomes seven and `scripts/check_receipts.py` needs its `EXPECTED_FILM_ASSETS` updated in the same commit. |
| 4 | **Whether to publish the ladder as the front page.** | Currently yes, labelled as published and attributed. The alternative is to lead with the first-party numbers instead, which is a worse page today and a much better one after §4a. |
| 5 | **Whether to publish `LAUNCH-PACKET.md`.** | Recommend it does not go out with the flip — it names gaps and the un-measured ladder. The owner's call. |
| 6 | **The asset filenames.** `FILM-WAR-30s-1080p.mp4` is 1920×1056 and 31.104 s. The names are already attached to the draft release and to the clips index. Renaming means re-uploading the assets; leaving them means the names stay slightly wrong. |

---

## 6. Launch assets

| Asset | Location | Notes |
|---|---|---|
| Draft release `v0.1.0` | GitHub, unpublished | 6 assets attached; body updated this pass |
| Demo video | `/home/clawerdigi2/AgentHub/model-acceleration/MODEL-ACCELERATION-DEMO.mp4` | See §6a |

### 6a. Demo video

| | |
|---|---|
| **File** | `MODEL-ACCELERATION-DEMO.mp4` |
| **Duration** | see the file's own metadata; the length is fixed by the script in `scripts/make_demo.py` |
| **Coverage** | The acceleration story end to end: the origin and the link; what the three node packs are and who wrote them; the install; the recipe; the stock-vs-accelerated workflow pair; the published ladder on screen with its provenance; what we measured ourselves and the 1.17×; the corrupt encoder; the craft gates; the curated set; the checker; and where the gaps are. |
| **Numbers on screen** | Only numbers verified against a receipt in `receipts/`. The published ladder is labelled as published on screen, with the upstream host. |
| **Published** | **No.** Not uploaded, not linked. The owner publishes. |

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
