#!/usr/bin/env bash
# One-shot installer: MiniMax-H3 + full acceleration stack on a single DGX Spark (GB10, sm_121).
#
#   curl -fsSL https://raw.githubusercontent.com/drowzeys/<REPO>/main/install.sh | bash
#   or:  ./install.sh [--comfy-dir ~/comfy] [--skip-weights]
#
# What it does, in order:
#   1. ComfyUI checkout + deps against system python (torch >= 2.9, cu13)
#   2. MiniMax-H3 weights from Comfy-Org/MiniMax-H3 (~41 GB; skip with --skip-weights)
#   3. Sol-Attn (KingGore) vendored PRE-PATCHED for sm_121  [Apache-2.0]
#   4. Sol-Attn (kijai) cloned from upstream               [no license file -> not vendored]
#   5. FirstBlockCache node + batched VAE decode           [this repo, Apache-2.0]
#   6. The Motion Context and FirstBlockCache node packs   [this repo, Apache-2.0]
#   7. Launcher + the tuned full-stack workflow
set -euo pipefail

COMFY_DIR="${HOME}/comfy"
SKIP_WEIGHTS=0
# The Motion Context pack refuses to run on a ComfyUI older than 0.34.0, because
# 0.34.0 changed the H3 latent layout it reads. v0.41.0 is the revision the
# 30-second films were rendered on.
COMFY_TAG="${COMFY_TAG:-v0.41.0}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKS_DIR="$(cd "$REPO_DIR/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --comfy-dir) COMFY_DIR="$2"; shift 2 ;;
    --skip-weights) SKIP_WEIGHTS=1; shift ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

say() { printf "\n\033[1;32m==>\033[0m %s\n" "$*"; }
die() { printf "\n\033[1;31mERROR:\033[0m %s\n" "$*"; exit 1; }

say "0/7 preflight"
python3 - <<'PY' || die "preflight failed — see the requirement printed above"
import sys, torch
cap = torch.cuda.get_device_capability()
print(f"  python {sys.version.split()[0]} | torch {torch.__version__} | device {torch.cuda.get_device_name(0)} sm_{cap[0]}{cap[1]}")
assert cap == (12, 1), f"this stack targets sm_121 (GB10 / DGX Spark); found sm_{cap[0]}{cap[1]}"
# The Sol-Attn kernels need Triton >= 3.3 for TMA descriptors; without it they fall
# back to slower pointer kernels, and torch < 2.6 fails kijai's requirement outright.
major, minor = (int(x) for x in torch.__version__.split(".")[:2])
assert (major, minor) >= (2, 6), f"torch >= 2.6 required (found {torch.__version__}); 2.11.0+cu130 is what this was benchmarked on"
try:
    from triton.tools.tensor_descriptor import TensorDescriptor  # noqa: F401
    print("  triton TMA descriptors: available")
except Exception:
    print("  triton TMA descriptors: MISSING — kernels will use the slower pointer path")
    print("    (update torch/triton to get the benchmarked numbers)")
PY
free -g | awk '/^Mem:/{print "  RAM total "$2"GB, available "$7"GB"}'

say "1/7 ComfyUI ${COMFY_TAG}"
mkdir -p "$COMFY_DIR" && cd "$COMFY_DIR"
[ -d ComfyUI ] || git clone --depth 100 https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
git fetch --tags origin -q
git checkout -q "$COMFY_TAG"
pip3 install -q -r requirements.txt --break-system-packages 2>&1 | tail -1 || true
grep __version__ comfyui_version.py

if [ "$SKIP_WEIGHTS" -eq 0 ]; then
  say "2/7 weights (~41 GB from Comfy-Org/MiniMax-H3)"
  command -v hf >/dev/null || pip3 install -q huggingface_hub --break-system-packages
  cd "$COMFY_DIR/ComfyUI/models"
  hf download Comfy-Org/MiniMax-H3 \
    diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors \
    text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors \
    vae/minimax_h3_video_vae_fp16.safetensors \
    vae/minimax_h3_audio_vae_fp32.safetensors \
    --local-dir .
  rm -rf .cache
else
  say "2/7 weights SKIPPED (--skip-weights)"
fi

say "3/7 Sol-Attn (KingGore), pre-patched for sm_121"
CN="$COMFY_DIR/ComfyUI/custom_nodes"
mkdir -p "$CN"
rm -rf "$CN/ComfyUI_sol-attn_Blackwell"
cp -r "$REPO_DIR/vendor/ComfyUI_sol-attn_Blackwell" "$CN/"

say "4/7 Sol-Attn (kijai) from upstream"
# Pinned to the commit this stack was benchmarked against. That repo is explicitly
# a work in progress, so an unpinned clone can pull a breaking change into a fresh
# install. Set KIJAI_REF=main to track upstream instead.
KIJAI_REF="${KIJAI_REF:-82e6fdfd1e983b621ab7e1ad19f27ae9669d3d45}"
if [ ! -d "$CN/ComfyUI-SolAttn_triton" ]; then
  git clone -q https://github.com/kijai/ComfyUI-SolAttn_triton.git "$CN/ComfyUI-SolAttn_triton"
fi
git -C "$CN/ComfyUI-SolAttn_triton" fetch -q origin
git -C "$CN/ComfyUI-SolAttn_triton" checkout -q "$KIJAI_REF" 2>/dev/null \
  || die "could not check out kijai ref $KIJAI_REF"
echo "  kijai @ $(git -C "$CN/ComfyUI-SolAttn_triton" log -1 --format=%h)"

say "5/7 FirstBlockCache + batched VAE decode (this repo)"
cp "$REPO_DIR/nodes/h3_fbc_node.py" "$REPO_DIR/nodes/h3_vae_batch.py" \
   "$CN/ComfyUI_sol-attn_Blackwell/"

say "6/7 Motion Context + FirstBlockCache node packs (this repo)"
# These two are node packs in their own right: each has an __init__.py, so
# ComfyUI loads it as a pack. The Sol-Attn pack is NOT copied in as a pack -
# its nodes are installed above, under the name ComfyUI loads them by.
for pack in H3-Motion-Context H3-FirstBlockCache; do
  [ -d "$PACKS_DIR/$pack" ] || die "$pack is not next to this installer"
  rm -rf "$CN/$pack"
  cp -r "$PACKS_DIR/$pack" "$CN/"
  echo "  $pack"
done

say "7/7 launcher + workflows"
# Point the launcher at THIS install, not the default path.
sed "s|^cd .*/ComfyUI$|cd ${COMFY_DIR}/ComfyUI|" \
    "$REPO_DIR/scripts/h3-comfy-launch.sh" > "$COMFY_DIR/h3-comfy-launch.sh"
chmod +x "$COMFY_DIR/h3-comfy-launch.sh"
cp "$REPO_DIR"/workflows/*.json "$COMFY_DIR/"

cat <<EOF

  Done. Start it:      ${COMFY_DIR}/h3-comfy-launch.sh
  Then open:           http://<this-host>:8188
  Tuned workflow:      ${COMFY_DIR}/h3-fullstack.json  (drag onto the canvas)
  Headless render:     curl -X POST http://127.0.0.1:8188/prompt \\
                         -H 'Content-Type: application/json' \\
                         -d "{\\"prompt\\": \$(cat ${COMFY_DIR}/h3-fullstack.json)}"

  Expect ~200 s for a 5-second 864x480 clip with audio on an idle GB10.
  NEVER launch with --use-sage-attention: it produces pure noise with H3.
EOF
