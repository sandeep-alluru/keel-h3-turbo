# The adapter shelf — turbo step-distillation LoRAs

Three step-distillation adapters that let H3 render in 4 or 8 sampling steps instead of 20.
Sizes and SHA-256 verified directly on the weights tree.

| File | Bytes | SHA-256 |
|---|---:|---|
| `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` | 1,956,192,992 | `c396a9a06f58399e9df9754b18299818d84a2ddd371724ba48fe4a41221437dc` |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | 1,956,193,000 | `2339acdf19bfe123f46b971ea35d367a84adb85de43627e1eceafa5a5b2b111e` |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` | 1,956,193,000 | `5b9ab5ade15d0775676d01a907268a69a1468dc6033b3b0d3ded5502f3ebb84c` |

All three are header-complete on disk and hash exactly as listed above.

## What a turbo adapter is

A LoRA that distils a 20-step sampler down to 4 or 8 steps. It is a different lever from the
attention and cache work: the kernel and cache optimisations make each step cheaper, the turbo
adapter makes there be fewer steps. They compose.

## What it measured

The turbo adapter is the largest first-party speedup we have recorded:

| Configuration | Steps | Wall | Against |
|---|---:|---:|---|
| Plain baseline, 1280×704 | 16 | 635 s | — |
| **Turbo 4-step LoRA, 1280×704** | **4** | **201 s** | **3.16×** |

Both figures come from `receipts/bench-matrix.tsv` (row `B5_turbo4_704` against
`BASELINE_16s_704`). The wall time includes the model load, which the matching run log records
as roughly 232 s.

**Two honest caveats.** First, this is a step-count reduction as much as it is an acceleration —
3.16× against a 16-step baseline, where the step count went down by 4×. Second, distilled steps
are a quality trade, not a free win: a 4-step LoRA render is not the same image as a 16-step
render of the same prompt, and no quality comparison is claimed here. The artefacts of that arm
were not retained.

## Where they are not

These adapters are not vendored in this repository. They are published weights, downloaded and
verified, like the DiT and the text encoder. The training-side recipe that produced our
own LoRAs is in [`../training/TRAINING.md`](../training/TRAINING.md).

## The names in the repo's own workflow config

The production workflow config in `production/H3-WORKFLOW-CONFIG.json` names the encoder as
`qwen3vl_32b_minimax_h3_nvfp4_awq-fresh-0543966f.safetensors`. That name is a local alias for the
clean NVFP4 encoder. The published file is
`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`, 15,687,142,551 bytes, SHA-256
`35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6`. Both names refer to the same
bytes; the `-fresh-` prefix marks the re-download after the corrupt copy, and that hash is the
one to check.
