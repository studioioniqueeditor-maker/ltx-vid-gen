# Use a RunPod base image that already has CUDA and Python optimized
FROM runpod/base:0.4.0-cuda12.1.0

# 1. Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*

# 2. Set working directory to /app
# This ensures we know exactly where our files are
WORKDIR /app

# 3. Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application code
COPY . .

# Set environment variables for better performance
ENV PYTHONUNBUFFERED=1
# Keep Hugging Face cache in workspace (volume mount friendly)
ENV HF_HOME=/workspace/hf_cache

# 5. Run the handler
# Use python3 and relative path since we are in WORKDIR
CMD [ "python3", "-u", "handler.py" ]
