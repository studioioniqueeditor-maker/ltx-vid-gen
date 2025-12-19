# Use a RunPod base image that already has CUDA and Python optimized
FROM runpod/base:0.4.0-cuda12.1.0

# 1. Install system dependencies
# Added libgl1-mesa-glx and libglib2.0-0 which are often needed for OpenCV/image libs
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Install Python requirements
COPY requirements.txt .
# --no-deps prevents it from trying to reinstall torch/torchvision if diffusers depends on them
# We verify torch manually in the handler
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/workspace/hf_cache

# 5. Run the handler
CMD [ "python3", "-u", "handler.py" ]