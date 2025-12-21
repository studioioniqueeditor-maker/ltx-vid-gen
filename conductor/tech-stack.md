# Technology Stack - LTX Video Generation Service

## Core ML & Runtime
*   **Python:** The primary programming language (3.10.5+ recommended).
*   **Lightricks/LTX-Video:** Custom repository for LTX-Video inference, specifically the 2B distilled FP8 version.
*   **FP8 Kernels:** Specialized kernels for high-performance generation on Ada/Hopper architectures.
*   **PyTorch:** Version >= 2.1.2 required.
*   **CUDA:** Version 12.2 required.

## Infrastructure & Deployment
*   **RunPod Serverless:** The target hosting platform for scalable, GPU-accelerated inference.
*   **Docker:** Used to package the service into lightweight "lite" images for rapid deployment and container startup.

## API & Validation
*   **FastAPI:** Provides the high-performance asynchronous web interface for the service.
*   **Pydantic:** Used for strict type validation and settings management for API requests.
*   **Uvicorn:** The ASGI server used to run the FastAPI application.

## Video & Image Utilities
*   **OpenCV (Headless):** Used for image pre-processing and resizing.
*   **imageio & imageio-ffmpeg:** Utilities for handling video container encoding and export.

## Performance Optimizations
*   **FP8 Quantization:** Optimized model execution to fit into GPU memory while maintaining inference speed.
