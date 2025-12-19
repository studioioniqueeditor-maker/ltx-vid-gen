# Use a RunPod base image that already has CUDA and Python optimized
FROM runpod/base:0.4.0-cuda12.1.0

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements first
COPY requirements.txt .

# 4. Install Python requirements
# Force upgrade pip and install requirements
# We install runpod explicitly again just to be paranoid
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt && \
    python3 -m pip install runpod

# 5. Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/hf_cache
# Ensure local bin is in path
ENV PATH="/usr/local/bin:$PATH"

# 6. Run the handler
# Explicitly use the python3 executable that has the packages installed
CMD [ "python3", "-u", "handler.py" ]
