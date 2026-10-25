# MiniMax-H3 + Sol-Engine stack for DGX Spark (GB10, sm_121, aarch64).
# Build ON the Spark: docker build -f docker/Dockerfile -t keys-h3-sm121:latest .
# Weights are NOT baked in (41 GB) — mount them:
#   docker run --rm --gpus all --network host \
#     -v $HOME/comfy/ComfyUI/models:/opt/comfy/ComfyUI/models \
#     -v $HOME/comfy/ComfyUI/output:/opt/comfy/ComfyUI/output keys-h3-sm121:latest
FROM nvcr.io/nvidia/pytorch:25.10-py3
ENV DEBIAN_FRONTEND=noninteractive PATH=/usr/local/cuda/bin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/comfy
RUN git clone --depth 100 https://github.com/comfyanonymous/ComfyUI.git \
    && cd ComfyUI && git fetch --tags -q && git checkout -q v0.30.1 \
    && pip install --no-cache-dir -r requirements.txt
RUN git clone --depth 1 https://github.com/kijai/ComfyUI-SolAttn_triton.git \
    /opt/comfy/ComfyUI/custom_nodes/ComfyUI-SolAttn_triton
COPY vendor/ComfyUI_sol-attn_Blackwell /opt/comfy/ComfyUI/custom_nodes/ComfyUI_sol-attn_Blackwell
COPY nodes/h3_fbc_node.py nodes/h3_vae_batch.py \
     /opt/comfy/ComfyUI/custom_nodes/ComfyUI_sol-attn_Blackwell/
COPY workflows/ /opt/comfy/workflows/
EXPOSE 8188
WORKDIR /opt/comfy/ComfyUI
CMD ["python3","main.py","--listen","0.0.0.0","--port","8188","--reserve-vram","8"]
# --- GB10 vLLM spin-wait fix -------------------------------------------------
# https://nacyot.github.io/artifacts/vllm-spin-wait-gb10/  (see GB10_SPIN_WAIT_PATCH.md)
# SpinCondition.wait() busy-loops 1s before sleeping; decode messages arrive every
# few ms, so CPU cores spin at max clock burning 10-20W. On GB10 the CPU and GPU
# share one SoC thermal budget, so that heat throttles the GPU. 1s -> 2ms.
# Guarded: never fails the build if this image has no vLLM at that path.
RUN f=$(find /usr/local/lib -name shm_broadcast.py -path "*device_communicators*" 2>/dev/null | head -1); \
    if [ -n "$f" ]; then sed -i 's/busy_loop_s: float = 1,/busy_loop_s: float = 0.002,/' "$f"; fi
