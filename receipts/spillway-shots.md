# Spillway shots — the three clips in `clips/`

`Spillway` is a short production that we ran on the local DGX Spark in October 2026. It was
stopped on 2026-10-25. Three rendered shots survive, and those three are the only video this
repository ships.

Everything below is copied from the production's own shot receipts. The three clips in
`clips/` are byte-identical to the artifacts those receipts point at, and
`scripts/check_receipts.py` re-hashes them on every run.

## The three shots

| Shot | Take | Event | Wall seconds | Clip SHA-256 | Bytes |
|---|---:|---|---:|---|---:|
| **S01** | 5 | `LOCKED` | 710.1506812029984 | `98c964bfa6e183ffff73d2df122e3911c84e43c6a2466a5caa08e6ab06622c29` | 4,421,601 |
| **S02** | 2 | `LOCKED` | 710.1323577519506 | `2e836122d14b24195ec41d9fe1cab26e4afca9ca16cebdc8ac817a77c2695857` | 5,649,982 |
| **S03** | 2 | `SELECTED` | 710.1413710840279 | `ca41bef4c9e3d75434cef9dd87a6f37dda3afb72bf21c600982fe6d637db29b8` | 4,058,738 |

### How each shot got its status — this matters, so it is spelled out

The production stop record names two locked shots and one shot selected during the run. The event
fields above are the receipt's own wording.

* **S01 take 5 — locked shot, carries an explicit sign-off.** `event: LOCKED`.
  Verdict note: *"Fine masonry tremor precedes the figure looking down, withdrawing hand and turning
  to reservoir. Full-rate opening check resolves ambiguous sparse sampling: stone features
  oscillate together, with stable photographic surface, intact hand and consistent set. No added
  chunks. Native audio quality remains unverified for finishing."*

* **S02 take 2 — locked shot, carries an explicit sign-off, after a source-grounded re-check.**
  `event: LOCKED`.
  Verdict note: *"Source-grounded re-check corrects invented bare-tail requirement. Actual spiked
  tail, pale membranes, two wingbeat rise, falling water and figure scale/reaction retained.
  Previous rejection preserved in ledger."* The earlier rejection of this shot is preserved in the
  production ledger; the re-check is what carried it.

* **S03 take 2 — selected shot, carries the selection record only, with no sign-off.**
  `event: SELECTED`, and the production stop record is explicit:
  `signed_off_by_this_order: false`.
  Verdict note: *"Selected after three rendered alternatives. Clear mouth-connected flyby and
  figure cover; exposed platform fire fades to persistent smoke/embers/scorch, preserving
  next-shot transition. Technical/creative/reference visual PASS; audio/finish pending."*

An earlier revision of this repository described all three as "3 of 15 shots locked". That was
wrong, and it is corrected here and in `clips/INDEX.md`: **two** shots carry an explicit sign-off,
and the third is an auto-selected shot made during the run.

## Render settings — identical across all three

```json
{
  "width": 1024, "height": 576, "frames": 192, "fps": 24, "steps": 20,
  "cfg": 1, "sampler": "euler", "scheduler": "simple",
  "shift_video": 12, "shift_audio": 3, "first_only": true,
  "accelerate": false
}
```

**`accelerate` is `false` on all three.** These clips were rendered with the acceleration stack
switched off. They are evidence that the production harness, the gates and the curation work; they
are not evidence that the acceleration stack is faster. The one speed claim this repository makes
about its own hardware is the SageAttention A/B in `receipts/sage-attention-ab.md`, and that
result was **no measurable gain**.

## Measured motion metrics

All three passed the technical, creative and reference checks: decode, frame count, duration,
dimensions, motion mean, motion p95, motion structure and audio presence.

| Shot | Motion mean | Motion p95 | Motion structure | Duration | Frames | Verdict |
|---|---:|---:|---:|---:|---:|---|
| S01 | 4.372 | 8.809 | 0.863 | 8.0 s | 192 | technical PASS |
| S02 | 2.658 | 4.555 | 0.845 | 8.0 s | 192 | technical PASS |
| S03 | 2.577 | 6.066 | 0.929 | 8.0 s | 192 | technical PASS |

`visual_verdict` and `audio_perceptual_verdict` are both `UNVERIFIED` on all three — the
receipts cover the technical gates, and native audio was never put through a perceptual assessment.

For scale: the motion gate in `craft/gates/motion_gate.py` was calibrated against our own
clips, where a visibly moving control sat at mean 3.13–3.65 and clips rejected as static at mean
0.07–0.89. All three shots sit inside the moving band.

## The production stop

```
PRODUCTION STOP 2026-10-25T14:35:34.064869+00:00
No production. Resume only on an explicit instruction.
```

The production stop record adds:

```json
{
  "authority": "Explicit instruction: STOP THE FILM NOW",
  "locked_shots": { "S01": 5, "S02": 2 },
  "s03_auto_selected_shot": {
    "take": 2, "commit": "928f867", "signed_off_by_this_order": false
  },
  "s04_prompt": "46e5fa12-3530-40c7-b43f-b9732ce4965a",
  "s04_receipt_event": "ERROR",
  "s04_verdict": "FAILED_RUNTIME",
  "s04_last_retained_sampling_step": 4,
  "s04_total_steps": 20,
  "queue_running": 0,
  "queue_pending": 0,
  "cancellation_issued_by_this_agent": false,
  "interruption_issuer": "UNVERIFIED",
  "resume_authority": "explicit instruction only"
}
```

S04 stopped at sampling step 4 of 20 with a runtime error, and the record attributes the
interruption to no one — `interruption_issuer` is `UNVERIFIED`. Only an explicit instruction can
resume production. Nothing in this repository resumes it.

## What this means for how you read the clips

These are shots from a stopped production, not a finished film. They exist here because they are
the honest output of the harness we built: one shot chosen by eye and signed off, one shot
carried back by a source-grounded re-check, and one shot selected automatically and filed
honestly as such.
