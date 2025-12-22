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

# Install Q8 Kernels (Required for FP8 inference)
WORKDIR /workspace
RUN git clone https://github.com/Lightricks/LTXVideo-Q8-Kernels.git
WORKDIR /workspace/LTXVideo-Q8-Kernels
RUN pip install -e .

# Install handler dependencies
WORKDIR /workspace
COPY requirements.txt .
RUN pip install -r requirements.txt huggingface_hub

# Set python path to include LTX-Video
ENV PYTHONPATH="${PYTHONPATH}:/workspace/LTX-Video"

# Copy application code
COPY . .

# Start the handler
CMD ["python", "-u", "handler.py"]
