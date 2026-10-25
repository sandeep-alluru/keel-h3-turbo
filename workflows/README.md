# The A/B pair

Two ComfyUI workflows, identical except for the acceleration nodes.

| | File | Acceleration |
|---|---|---|
| Control | `h3-dense-baseline.json` | none — stock ComfyUI |
| Treatment | `h3-fullstack.json` | `SolAttnPatch` (tau 1.3, INT8 QK) → `H3FirstBlockCache` (threshold 0.08) |

Both use the same prompt, the same seed (**46**), the same geometry (**864×480**, **124 frames**),
the same **20** steps, the same scheduler (`simple`) and sampler (`res_multistep`), and the same
checkpoint.

## What these are, and what they are not

They are the upstream port's own workflows with **one fix**. Upstream ships the dense control at
seed 46 and the full stack at seed 45, which makes the pair unusable as an A/B — different noise,
different result, no attribution. Their own bench notes say *"Same prompt and seed 46 across the
ladder unless noted"*, so the seed 45 in the shipped full-stack file is the outlier, not the
control. Both files here use 46.

The upstream files are left untouched at
`custom_nodes/H3-SolAttn-SM121/workflows/`, because that tree is vendored as its authors shipped
it. The corrected pair lives here.

The only other change is the output filename prefix, so a dense run and a full-stack run cannot
overwrite each other.

## The batched VAE decode is not a graph node

The upstream full stack has three parts, and only two of them are nodes:

* `SolAttnPatch` — a node.
* `H3FirstBlockCache` — a node.
* **batched VAE tile decode** — a monkeypatch applied on import to
  `MiniMaxH3VideoVAE.tiled_decode`, installed by `install.sh` as `h3_vae_batch.py`.

It is **on by default** and is turned off with `H3_VAE_BATCHED=0`. If you run this pair and the
batched decode is disabled, your treatment is not the full stack and the comparison is void.

```bash
echo "${H3_VAE_BATCHED:-0}"     # 0 means the patch is disabled
```

## Which checkpoint

Both workflows load `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (34,038,892,334 bytes),
because that is the checkpoint the published ladder was measured on.

For production on one Spark, swap it for `minimax_h3_fl2va_pruned_fp8_scaled.safetensors`
(20,958,205,608 bytes) — the FP8 pair is what leaves room for the encoder and both VAEs in
unified memory. `receipts/checkpoint-sizes.md` has the full table.

## Before you run

* GPU idle: `nvidia-smi --query-compute-apps` must be empty.
* 864×480 × 124 frames is the benchmarked workload. 362 frames is the practical ceiling for one
  Spark — 2.9× the frames costs 6.5× per step.
* Queue the control, let it finish, then queue the treatment. Never queue both at once: a
  contended run is a different experiment, not a slower one.

`RECIPE.md` has the full procedure, including how to file the result as a first-party receipt.
