# Training on the Spark

The training side of the stack, proven on the same GB10 hardware the inference stack runs on. Tooling: Ostris **ai-toolkit**, bf16, single GPU.

## FLUX.1-schnell LoRA pilot — a full 500-step run

Purpose: prove the training pipeline end-to-end on the DGX Spark before pointing it at production work. Config: [`train-schnell.yaml`](train-schnell.yaml).

| Setting | Value |
|---|---|
| Base | FLUX.1-schnell (local download; the weights are gated) |
| Adapter | LoRA rank 16 / alpha 16, via `ostris/FLUX.1-schnell-training-adapter` |
| Steps | 500 |
| Optimizer | AdamW, lr 5.0e-5 |
| Precision | bf16, batch 1, flowmatch noise scheduler |
| Dataset | captioned motion-graphic frames at 1024 (trigger word in captions) |
| Saves | every 250 steps (final + step-250 kept) |
| Samples | every 250 steps, 1024×576, 4 steps |

**Outcome — the run completed.** Artefacts on disk: the final adapter and the step-250 checkpoint (**171,970,368 bytes each**), optimizer state (688,175,607 bytes), and sample generations at steps 0 / 250 / 500 in the run log, which prints per-step loss throughout (train.log, retained with the project archive).

Deliberate minimalism, per the run spec: no 8-bit optimizer, no quantization, no gradient checkpointing, no EMA — on 128 GB of unified memory none of it is needed, and every addition is a variable.

## Persona LoRA programme

The production persona pipeline that feeds the film work runs the same recipe shape: rank-16 LoRA, 500 steps, lr 5.0e-5, a captioned 1024px identity dataset, with run logs and **reload-verification artefacts** (the trained adapter is re-loaded and re-rendered — `final-reload.json` plus smoke/reload renders — before it is admitted to production). The config file itself is not reproduced in this repo: it carries persona sample prompts. The inference-side gates that judge its output are in [`../craft/gates/`](../craft/gates/).

## H3 turbo adapters

The step-distillation LoRAs the H3 stack deploys (4-step and 8-step FL2V, 4-step Ref2V) are catalogued with sizes and SHA-256 hashes in the [README adapter shelf](../README.md#the-adapter-shelf--turbo-step-distillation-loras).
