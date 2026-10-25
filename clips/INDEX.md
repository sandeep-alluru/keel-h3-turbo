# The curated set — six clips, and only six

This set is final. Six clips: three finished films and three Spillway shots. Proof renders, test
clips and rejected takes are not here and should not be added.

`scripts/check_receipts.py` enforces the set on every run — it re-hashes each clip against the
hash below and fails if a seventh video appears.

---

## 1 — `spillway-s01.mp4` · Spillway S01, take 5

| | |
|---|---|
| Status | **Locked shot** — carries an explicit sign-off |
| Geometry | 1024×576, 192 frames, 24 fps, 8.0 s |
| Settings | 20 steps, cfg 1, euler/simple, `accelerate: false` |
| Wall time | 710.1506812029984 s |
| Bytes | 4,421,601 |
| SHA-256 | `98c964bfa6e183ffff73d2df122e3911c84e43c6a2466a5caa08e6ab06622c29` |
| Motion | mean 4.372 · p95 8.809 · structure 0.863 |

The opening shot of the reservoir. A fine masonry tremor, then the figure looks down, withdraws a
hand and turns to the reservoir. The assessment note records that a full-rate pass was needed to
resolve an ambiguous sparse sample, and that the stone features oscillate together with a stable
photographic surface and an intact hand.

Receipt: `receipts/shot-receipt.json` · `receipts/spillway-shots.md`

---

## 2 — `spillway-s02.mp4` · Spillway S02, take 2

| | |
|---|---|
| Status | **Locked shot** — carries an explicit sign-off, after a source-grounded re-check |
| Geometry | 1024×576, 192 frames, 24 fps, 8.0 s |
| Settings | 20 steps, cfg 1, euler/simple, `accelerate: false` |
| Wall time | 710.1323577519506 s |
| Bytes | 5,649,982 |
| SHA-256 | `2e836122d14b24195ec41d9fe1cab26e4afca9ca16cebdc8ac817a77c2695857` |
| Motion | mean 2.658 · p95 4.555 · structure 0.845 |

A spiked tail, pale membranes, two wingbeats of rise, falling water, and the figure's scale and
reaction. This shot was **rejected once and then carried**: a source-grounded re-check corrected
an invented "bare tail" requirement, and the previous rejection is preserved in the production
ledger rather than overwritten.

Receipt: `receipts/spillway-shots.md`

---

## 3 — `spillway-s03.mp4` · Spillway S03, take 2

| | |
|---|---|
| Status | **Selected shot** — carries the selection record only, with no sign-off |
| Geometry | 1024×576, 192 frames, 24 fps, 8.0 s |
| Settings | 20 steps, cfg 1, euler/simple, `accelerate: false` |
| Wall time | 710.1413710840279 s |
| Bytes | 4,058,738 |
| SHA-256 | `ca41bef4c9e3d75434cef9dd87a6f37dda3afb72bf21c600982fe6d637db29b8` |
| Motion | mean 2.577 · p95 6.066 · structure 0.929 |

A clear mouth-connected flyby and cover; exposed platform fire fades to persistent smoke, embers
and scorch, which preserves the transition into the next shot. Chosen after three rendered
alternatives. It is filed here as the selection it was — the production stop record states plainly
that this take was **not** signed off.

Receipt: `receipts/spillway-shots.md`

---

## 4–6 — the three finished films

These ship as release assets rather than as files in this repository. They are listed here so the
set is complete in one place, with the geometry and hash measured on the actual files.

### 4 — `FILM-WAR-1920x1056.mp4`

| | |
|---|---|
| Measured geometry | 1920×1056, 744 frames, 24 fps, **31.104 s** |
| Codec | H.264 video + AAC stereo, 32 kHz |
| Bytes | 75,251,626 |
| SHA-256 | `18cdfd1f4e5ae550b8c854efb71832802eddf4a3a47bbe547d7bd09e03c7c627` |

### 5 — `FILM-BEACON-1920x1056.mp4`

| | |
|---|---|
| Measured geometry | 1920×1056, 744 frames, 24 fps, **31.104 s** |
| Codec | H.264 video + AAC stereo, 32 kHz |
| Bytes | 74,441,993 |
| SHA-256 | `03b4500d0fab85cf11e1cf859a16b77326900a4637042b81faea3f119104e220` |

### 6 — `FILM-BRIDGE-1920x1056.mp4`

| | |
|---|---|
| Measured geometry | 1920×1056, 744 frames, 24 fps, **31.104 s** |
| Codec | H.264 video + AAC stereo, 32 kHz |
| Bytes | 76,399,114 |
| SHA-256 | `64a2b1c86b3bc89594ad1cadf4b0b0cad5f3adaf3dfab0175df78ce2cd6b18c2` |

**A note on the filenames.** The release assets are named for the measured geometry. The files
contain 744 frames at 24 fps — 31.0 s of video, **31.104 s** of container duration — at 1920×1056,
which is not 1080p. The names above are the measured ones; the numbers in the tables are what the
files contain.

---

## About these six

* **Rendered with the acceleration stack switched off.** All three Spillway shots record
  `"accelerate": false`. They are the evidence for the production harness and the craft gates.
* **Three shots from a stopped production.** The Spillway production stopped on 2026-10-25, after
  S04 was rejected at sampling step 4 of 20. These are the three shots from that run rather than an
  edit.
* **The curated six.** The record contains a fourth published film and several earlier cuts. The
  set above is the curated six, and it stays six.
* **The speed numbers live elsewhere.** The only speed measurement taken on this hardware is the
  SageAttention A/B, which found no measurable gain.
