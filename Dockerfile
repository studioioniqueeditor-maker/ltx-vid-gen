# ==========================================
# LTX Video I2V - RunPod Serverless Dockerfile
# Simplified version without database/webhooks
# ==========================================

FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Clone LTX-Video repository and install
RUN git clone https://github.com/Lightricks/LTX-Video.git && \
    cd LTX-Video && \
    pip install --no-cache-dir -e .[inference-script]

# Install FP8 kernels for faster inference (optional but recommended)
RUN pip install --no-cache-dir git+https://github.com/Lightricks/LTXVideo-Q8-Kernels.git || \
    echo "Warning: FP8 kernels installation failed, continuing without them"

# ==========================================
# CRITICAL: Download model weights during build
# ==========================================
# This is essential for fast cold starts (<2s)
# Model size: ~26GB
# Build time: ~10-15 minutes (one-time cost)

RUN echo "Downloading LTX Video 13B Distilled model..." && \
    pip install --no-cache-dir huggingface_hub && \
    huggingface-cli download Lightricks/LTX-Video-0.9.8-13B-distilled \
    --local-dir /workspace/models/ltxv-13b-distilled && \
    echo "✓ Model weights downloaded successfully"

# Verify model files exist
RUN ls -lh /workspace/models/ltxv-13b-distilled/ && \
    echo "✓ Model verification complete"

# Copy application code
COPY config.py .
COPY validation.py .
COPY utils.py .
COPY storage.py .
COPY generate_i2v.py .
COPY handler.py .

# Copy Oracle Cloud private key (you'll add this before building)
COPY oci_private_key.pem /workspace/oci_private_key.pem
RUN chmod 600 /workspace/oci_private_key.pem

# Create necessary directories
RUN mkdir -p /tmp/outputs /tmp/uploads && \
    chmod 777 /tmp/outputs /tmp/uploads

# Set environment variables
ENV MODEL_PATH=/workspace/models/ltxv-13b-distilled \
    OUTPUT_DIR=/tmp/outputs \
    UPLOAD_DIR=/tmp/uploads \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import torch; assert torch.cuda.is_available()" || exit 1

# Near the end, before CMD
ARG OCI_PRIVATE_KEY_BASE64
RUN if [ -n "$OCI_PRIVATE_KEY_BASE64" ]; then \
      echo "$OCI_PRIVATE_KEY_BASE64" | base64 -d > /workspace/oci_private_key.pem && \
      chmod 600 /workspace/oci_private_key.pem; \
    fi

# RunPod serverless handler
CMD ["python", "-u", "handler.py"]
