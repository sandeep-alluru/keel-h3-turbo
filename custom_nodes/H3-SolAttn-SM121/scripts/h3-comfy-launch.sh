#!/bin/bash
# MiniMax H3 ComfyUI launch — DGX Spark GB10 (sm_121)
# Sol-Attn plugin (custom_nodes/ComfyUI_sol-attn_Blackwell) patched for compute cap 12.1.
# Do NOT add --use-sage-attention: known to produce pure noise with H3 (ComfyUI #15263).
#
# --disable-comfy-compiler turns off ComfyUI's model compiler and its CUDA-graph
# subfeature. ComfyUI 0.41.0 plans the H3 model's allocations up front, and on a
# Spark that is running other work the plan does not fit the memory that is left;
# the sampler then stops with "aimdo memory compile error". Everything else in
# the stack is unaffected.
export PATH=/usr/local/cuda-13.0/bin:$PATH
cd ~/comfy/ComfyUI
exec python3 main.py --listen 0.0.0.0 --port 8188 --reserve-vram 8 --disable-comfy-compiler "$@"
