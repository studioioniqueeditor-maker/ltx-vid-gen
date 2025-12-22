#!/bin/bash
set -e

# Install Q8 Kernels at runtime to ensure compatibility with the specific GPU (A100/H100)
# and to avoid build-time failures on CPU runners.
if [ -d "/workspace/LTXVideo-Q8-Kernels" ]; then
    echo "Installing LTXVideo-Q8-Kernels..."
    cd /workspace/LTXVideo-Q8-Kernels
    pip install -e .
    cd /workspace
fi

# Start the python handler
echo "Starting Handler..."
python -u handler.py
