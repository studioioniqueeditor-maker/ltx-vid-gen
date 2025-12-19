# LTX Video Generation Deployment Guide for RunPod Serverless

This guide provides step-by-step instructions for deploying your `ltx-vid-gen` project on RunPod Serverless, using the optimized FP8 model and Base64 output.

---

## Part 1: Local Setup & Image Build

1.  **Build the Docker Image**:
    ```bash
    docker build --platform linux/amd64 -t my-ltx-vid-gen-lite:latest .
    ```

2.  **Push to Docker Hub**:
    ```bash
    docker tag my-ltx-vid-gen-lite:latest YOUR_DOCKERHUB_USERNAME/ltx-vid-gen-lite:v0.2.0-lite
    docker push YOUR_DOCKERHUB_USERNAME/ltx-vid-gen-lite:v0.2.0-lite
    ```

---

## Part 2: Model Setup (FP8 Weights)

1.  **Create Network Volume**:
    *   Size: **50GB** (or more).
    *   Data Center: Note this location (e.g., `US-NJ`).

2.  **Download Weights**:
    *   Spin up a temporary Pod in the **same Data Center** with the volume mounted at `/workspace/ltx-models`.
    *   Run this command in the Web Terminal to download the FP8 weights and config:

    ```bash
    # Clean up
    rm -rf /workspace/ltx-models/*

    # Download FP8 model file
    python3 -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='Lightricks/LTX-Video', filename='ltxv-13b-0.9.8-distilled-fp8.safetensors', local_dir='/workspace/ltx-models')"
    
    # Download configuration files
    python3 -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Lightricks/LTX-Video', local_dir='/workspace/ltx-models', allow_patterns=['scheduler/*', 'tokenizer/*', 'text_encoder/*', 'vae/*', 'model_index.json', '*.json'])"
    ```

    *   **Terminate** the temporary pod when done.

---

## Part 3: Serverless Deployment

1.  **Create Endpoint**:
    *   **Data Center**: Same as your volume.
    *   **GPU**: NVIDIA A100 80GB (Recommended).
    *   **Template / Image**: `YOUR_DOCKERHUB_USERNAME/ltx-vid-gen-lite:v0.2.0-lite`.
    *   **Container Disk**: `20GB`.
    *   **Network Volume**: Select your volume, mount at `/workspace/ltx-models`.
    *   **Idle Timeout**: `300` seconds.

2.  **Environment Variables**:
    *   None required! (Unless you changed defaults).

3.  **Test**:
    *   Send a request. The response will contain `"video_base64": "..."`.
    *   Your client app should decode this string to save the `.mp4` file.
