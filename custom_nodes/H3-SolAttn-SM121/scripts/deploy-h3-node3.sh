#!/bin/bash
# Deploy the tuned MiniMax H3 stack to node3 (gx10-5185, fabric <node3-ip>).
# Mirrors the head node's setup: ComfyUI v0.30.1 + Sol-Attn (kijai + KingGore/sm_121 patches)
# + ported FirstBlockCache + batched VAE decode. Weights are rsynced over the 200G fabric.
#
# Prereq: node3 must have its GPU free (stop dsv4f-v026-opt first).
# Usage: ~/comfy/deploy-h3-node3.sh
set -euo pipefail
N3=<node3-ip>
say() { echo -e "\n=== $* ==="; }

say "1/5 preflight"
ssh keyspark@$N3 'free -g | awk "/^Mem:/{print \"  mem_avail=\"\$7\"GB\"}"; df -BG --output=avail / | tail -1 | tr -d " " | sed "s/^/  disk_avail=/"; nvidia-smi --query-compute-apps=pid --format=csv,noheader | wc -l | sed "s/^/  gpu_procs=/"'

say "2/5 ComfyUI checkout + deps"
ssh keyspark@$N3 'set -e
  mkdir -p ~/comfy && cd ~/comfy
  [ -d ComfyUI ] || git clone --depth 50 https://github.com/comfyanonymous/ComfyUI.git
  cd ComfyUI && git fetch --tags origin -q && git checkout -q v0.30.1
  pip3 install -q -r requirements.txt --break-system-packages 2>&1 | tail -1 || true
  grep __version__ comfyui_version.py'

say "3/5 sync weights over fabric (~41 GB, resumable)"
rsync -a --info=progress2 --partial \
  ~/comfy/ComfyUI/models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors \
  keyspark@$N3:~/comfy/ComfyUI/models/diffusion_models/
rsync -a --info=progress2 --partial \
  ~/comfy/ComfyUI/models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors \
  keyspark@$N3:~/comfy/ComfyUI/models/text_encoders/
rsync -a --info=progress2 --partial \
  ~/comfy/ComfyUI/models/vae/minimax_h3_video_vae_fp16.safetensors \
  ~/comfy/ComfyUI/models/vae/minimax_h3_audio_vae_fp32.safetensors \
  keyspark@$N3:~/comfy/ComfyUI/models/vae/

say "4/5 sync tuned plugins (sm_121 patches, FBC, batched VAE) + workflows"
rsync -a ~/comfy/ComfyUI/custom_nodes/ComfyUI_sol-attn_Blackwell \
         ~/comfy/ComfyUI/custom_nodes/ComfyUI-SolAttn_triton \
         keyspark@$N3:~/comfy/ComfyUI/custom_nodes/
rsync -a ~/comfy/h3-fullstack.json ~/comfy/h3-t2v-api.json keyspark@$N3:~/comfy/
ssh keyspark@$N3 'cat > ~/comfy/h3-comfy-launch.sh <<"EOF"
#!/bin/bash
# MiniMax H3 ComfyUI — node3 replica (GB10 sm_121). Never use --use-sage-attention with H3.
export PATH=/usr/local/cuda-13.0/bin:$PATH
cd ~/comfy/ComfyUI
exec python3 main.py --listen 0.0.0.0 --port 8188 --reserve-vram 8 "$@"
EOF
chmod +x ~/comfy/h3-comfy-launch.sh'

say "5/5 launch + verify"
ssh keyspark@$N3 'cd ~/comfy && nohup ./h3-comfy-launch.sh > ~/comfy/comfyui.log 2>&1 & sleep 30
  grep -E "H3-VAE|Sol-Attn nodes|To see the GUI" ~/comfy/comfyui.log | tail -3'
echo
echo "node3 ComfyUI: http://<node3-ip>:8188  (mgmt: http://<mgmt-ip>:8188)"
