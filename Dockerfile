# Use a RunPod base image that already has CUDA and Python optimized
FROM runpod/base:0.4.0-cuda12.1.0

# 1. Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*

# 2. Install Python requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy only the code
COPY . .

# Set environment variables for better performance
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/workspace/hf_cache

CMD [ "python", "-u", "/handler.py" ]