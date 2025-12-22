FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Clone LTX-Video repository
RUN git clone https://github.com/Lightricks/LTX-Video.git

# Install LTX-Video dependencies
WORKDIR /workspace/LTX-Video
RUN pip install -e .[inference]

# Clone Q8 Kernels (Install at runtime via start.sh)
WORKDIR /workspace
RUN git clone https://github.com/Lightricks/LTXVideo-Q8-Kernels.git

# Install handler dependencies
WORKDIR /workspace
COPY requirements.txt .
RUN pip install -r requirements.txt huggingface_hub

# Set python path to include LTX-Video
ENV PYTHONPATH="${PYTHONPATH}:/workspace/LTX-Video"

# Copy application code
COPY . .

# Grant execution permissions to start script
RUN chmod +x start.sh

# Start using the shell script
CMD ["./start.sh"]
