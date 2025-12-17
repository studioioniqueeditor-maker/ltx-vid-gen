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

RUN printf "-----BEGIN PRIVATE KEY-----" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "-----BEGIN PRIVATE KEY-----" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDBMfHt1Ta2yFBM" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "1hk+cXzpS2DevDXvE0u7AMxq8LOeYkGz/POOwk7Z2Cj4E1OVrmSpaOT/Kj/jYszR" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "57JslF1CC+nhI28iIjdWI04yle9D+F3aI7J4+YqdpDgb0tqLoOJtBxnPsgSchcMA" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "bn2MplvSceSvPRqS+71u+hZ97PgJxTQkMFA47pEJOAudx1w2pZZqIAviYBS5k4mD" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "G5LKekymPKuATHbTsoBhx1WF0GV+DYsLUBOKgum1oPQ/NFApYxPcNjg9zd9TWtry" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "E4vqDzAplknc/amX3YUYs1xMo5BEq7go3YASukmdzGQlbo+rCfTDYpM139L59DOL" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "/k/o6YvFAgMBAAECggEADkzXHoagtSjgoL9cQP3/g/k7Y2FFELw5586oUuYcNYYK" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "XPtFP/TsBz3z0mED19l/w/ZqtOR4tCkVBhiDYXwd5wygtDR+PmWP+QVF/YKRolNZ" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "BxOLW18FPqPwL0cNPDada/qRk4kWxEs2YurKykVqGIqrpbj9JZIStIs4bPvEZFye" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "hQhOyuAU52tCZ4NBUhzb2CKAxQ/gy89KDtijHM/Fv2zuK5flmwMwLynB5JHQm9qc" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "3Tv/1K6SuqfJWg3mdWNeEdWnF5K28F5uYVPcUmah+uKw/hwIUeTI+JaGNiMl3YcA" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "RW6GymPVMTQ8PZXlwbfihhrN9IBH4Uz/3EjjsaZQoQKBgQDrJAcs5ZcE+bDdvyXc" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "p6g0Tj+qCv+NKJGyPfR7lV4SWyaDhf8XOnr0oH+RGuDCYhasFoLizYr5lfyIo5vK" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "HC3ogCj+yfrwOsQ2XQAQGZzbARBtIm0oBDG8H3LclNKpvXbPe1eUj0E4dMBD4gU5" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "D+JA7+UwmS8qXiyUOEQN8QBJiQKBgQDSVVhF70qupzAdGZiJJM1BwnYaaP7NWStT" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "wOurvRyDy41WjF+RykDt1zyhGHfH9kXi7BnrGFlwqmg01pUQ/JfvgTfeWt9p/8QK" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "ZLlCzlaN3IwzjNyv6kPvh97GSvraxukIUY0V13Q753swXlF3jnSvV0xot7J8TTUr" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "eeU3OiPtXQKBgQCs56Y7FmxRZUXwGQG/Wq1uIOfhowq9gsp39eTUB0bQWqRcbGji" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "bMdDIM4NJmWFqlkfm8INArWhx++VjjEdklETuUHr8RwMEDp9+y7zp9HWnNa2WW1I" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "0qS7v6hXmTu7Qy2dbgY9oIWF/RvwDsBmcE6gD4dJkCrFjdBcAW/RjJj4eQKBgFPH" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "GroAbkbS4R82KsO1nOwsgM5UM+mnMtLRbQ2i7dCxK0Ll9ssjPGl/6e5gyJUlSwDv" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "+gLiV/3AYnFpZ0a01e/YEGDI4WRfM77QD9rERUWMK2v9F4oaTaUDAYEKLJEn2Xou" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "wXuJrgqOUUsaxmhQnbmZlB3BzZ4lQqBmlR5CUj0hAoGBAJIIG/xDb1vOajeRggvl" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "44nK/XzujfDInI6oP2d7iDpKwkxwuIV/WLql/hr6d3gYQPfFTbIF/CqF9RsftqSD" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "Dn8uDJzX3L8h8zBvBGcozODFabmNrNckHR4PaCp3lYIlgbjB9Qekmnaaxzay+FRd" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "V+UE5MW374Lco2mpmpma2lXz" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "-----END PRIVATE KEY-----" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem
RUN echo -e "OCI_API_KEY" > /workspace/oci_private_key.pem && chmod 600 /workspace/oci_private_key.pem

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
