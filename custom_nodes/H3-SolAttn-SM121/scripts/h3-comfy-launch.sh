#!/bin/bash
# MiniMax H3 ComfyUI launch — DGX Spark GB10 (sm_121)
# Sol-Attn plugin (custom_nodes/ComfyUI_sol-attn_Blackwell) patched for compute cap 12.1.
# Do NOT add --use-sage-attention: known to produce pure noise with H3 (ComfyUI #15263).
export PATH=/usr/local/cuda-13.0/bin:$PATH
cd ~/comfy/ComfyUI
exec python3 main.py --listen 0.0.0.0 --port 8188 --reserve-vram 8 "$@"
