#!/bin/bash
# ============================================
# LTX Video 13B Setup Script for RunPod A40
# ============================================
# Run this script after starting your RunPod pod
# Usage: bash setup.sh

set -e  # Exit on error

echo "============================================"
echo "LTX Video 13B Setup for RunPod A40"
echo "============================================"

# 1. System updates
echo ""
echo "[1/6] Updating system packages..."
apt update && apt install -y git wget ffmpeg

# 2. Create workspace
echo ""
echo "[2/6] Setting up workspace..."
cd /workspace
mkdir -p ltx-video inputs outputs models
cd ltx-video

# 3. Clone LTX-Video repository
echo ""
echo "[3/6] Cloning LTX-Video repository..."
if [ ! -d "LTX-Video" ]; then
    git clone https://github.com/Lightricks/LTX-Video.git
fi
cd LTX-Video

# 4. Install Python dependencies
echo ""
echo "[4/6] Installing Python dependencies..."
pip install -e .[inference-script]
pip install huggingface_hub accelerate fastapi uvicorn python-multipart

# 5. Download model weights
echo ""
echo "[5/6] Downloading LTX Video 13B Distilled model..."
echo "This may take 10-15 minutes depending on connection speed..."

huggingface-cli download Lightricks/LTX-Video-0.9.8-13B-distilled \
    --local-dir /workspace/models/ltxv-13b-distilled

# 6. Install FP8 kernels for faster inference (optional but recommended)
echo ""
echo "[6/6] Installing FP8 kernels for faster inference..."
pip install git+https://github.com/Lightricks/LTXVideo-Q8-Kernels.git || echo "FP8 kernels install failed, continuing without them"

# Copy scripts to workspace
echo ""
echo "Setting up generation scripts..."
cd /workspace/ltx-video

# Create directories
mkdir -p /workspace/inputs
mkdir -p /workspace/outputs

echo ""
echo "============================================"
echo "SETUP COMPLETE!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Upload your images to /workspace/inputs/"
echo "2. Copy generate_i2v.py, batch_process.py, api_server.py to /workspace/ltx-video/"
echo "3. Update MODEL_PATH in generate_i2v.py if needed"
echo ""
echo "Quick test:"
echo "  cd /workspace/ltx-video"
echo "  python generate_i2v.py --image /workspace/inputs/test.jpg --prompt 'subtle motion' --output test"
echo ""
echo "Start API server:"
echo "  python api_server.py"
echo ""
echo "Estimated cost: ~\$0.50/hr on A40 Community Cloud"
echo "Expected speed: ~45 seconds per 720p video"
echo ""
