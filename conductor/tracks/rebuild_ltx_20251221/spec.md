# Specification: Rebuild LTX Video Service from Scratch (FP8 Distilled)

## 1. Overview
We will rebuild the LTX video generation service from scratch on a new branch. The goal is to provide a robust, error-free API that accepts an image and a prompt, and returns a generated video (downloadable or base64) using the **LTX-Video 2B distilled FP8 model**. The service will be optimized for RunPod A100 GPUs (80GB VRAM) using network volume storage for models.

## 2. Goals
*   **Zero Errors:** Achieve perfect generation reliability on the first attempt.
*   **Performance:** Generate a 5-second video efficiently using FP8 optimization.
*   **Infrastructure:** RunPod Serverless on A100 (80GB VRAM) with Network Volume.
*   **Input/Output:**
    *   Input: Image (URL/Base64) + Prompt (Text).
    *   Output: Downloadable video link or Base64 string (user preference: "download").

## 3. Technical Requirements
*   **Base Image:** RunPod pytorch container (CUDA 12.2, PyTorch >= 2.1.2).
*   **Core Repo:** `Lightricks/LTX-Video` (cloned during build/runtime or baked in).
*   **Model Config:** `configs/ltxv-2b-0.9.8-distilled-fp8.yaml`.
*   **Optimization:** FP8 Kernels (if supported/stable) or standard FP8 inference via the repo.
*   **Storage:** Models stored in `/workspace/ltx-models` (Network Volume).
*   **API:** FastAPI/RunPod Handler.

## 4. Implementation Steps
1.  **Clean Slate:** Remove old implementation files (but keep `conductor/`).
2.  **Environment Setup:** Create a new `Dockerfile` and `requirements.txt` strictly following the `ltx-guide-nblm.md`.
3.  **Model Management:** Create a script to download the specific 2B distilled model weights to the network volume if missing.
4.  **Inference Engine:** Implement `inference_handler.py` using the `ltx_video.inference` module as documented.
5.  **RunPod Handler:** Create `handler.py` to wrap the inference engine and handle I/O.
6.  **Testing:** Local testing script (mocking the RunPod environment) to verify the full pipeline.

## 5. Constraints
*   **VRAM:** 80GB available (plenty for 2B model, but ensure efficient loading).
*   **Network:** Models must be loaded from network volume to avoid download latency on cold starts.
*   **Resolution:** 1216x704 (or similar divisible by 32).
*   **Frames:** 121 frames ($8n+1$).
