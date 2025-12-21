# Deployment Guide: LTX Video Generation (RunPod Serverless)

This guide provides a detailed, step-by-step walkthrough for deploying the rebuilt LTX Video Generation service on RunPod Serverless, optimized for the 2B distilled FP8 model.

## 1. Build and Push the Docker Image

### Option A: Manual Build
1.  **Ensure Docker is installed** and you are logged into your registry:
    ```bash
    docker login
    ```
2.  **Build the image** from the project root:
    ```bash
    docker build -t your-username/ltx-vid-gen:latest .
    ```
3.  **Push the image** to the registry:
    ```bash
    docker push your-username/ltx-vid-gen:latest
    ```

### Option B: Automated CI/CD (GitHub Actions)
This repository includes a GitHub Action workflow (`.github/workflows/docker-publish.yml`) that automatically builds and pushes the image on every push to `main` or `rebuild-ltx`.

1.  Go to your GitHub Repository **Settings > Secrets and variables > Actions**.
2.  Add the following Repository Secrets:
    *   `DOCKER_USERNAME`: Your Docker Hub username.
    *   `DOCKER_PASSWORD`: Your Docker Hub Access Token (recommended) or password.
3.  Push your code to GitHub. The action will trigger and push the image to `docker.io/<your-github-username>/<repo-name>:latest` (or matching tag).

## 2. Prepare the RunPod Network Volume

Using a Network Volume ensures that model weights are persistent and shared across serverless workers, significantly reducing cold start times.

1.  **Create the Volume:**
    - Go to the **Network Volumes** section in your RunPod dashboard.
    - Click **Create Volume**.
    - Choose a name (e.g., `ltx-models-volume`) and a region (e.g., `us-east-1`).
    - Set the size (20 GB is sufficient for the 2B model).
2.  **Populate the Volume:**
    - Deploy a temporary **GPU Pod** (e.g., an RTX 4090 or A100) and mount the volume to `/workspace/ltx-models`.
    - Once the pod is running, open a terminal (SSH or Web Console).
    - Run the download script provided in this repository:
      ```bash
      export MODEL_PATH="/workspace/ltx-models"
      python3 download_models_distilled.py
      ```
    - Verify the files were downloaded correctly:
      ```bash
      python3 verify_models.py
      ```
    - **Terminate the GPU Pod** once the download is finished to save costs.

## 3. Create a RunPod Serverless Template

1.  Go to the **Templates** section and click **New Template**.
2.  **Template Name:** `LTX-Video-FP8`
3.  **Container Image:** `your-username/ltx-vid-gen:latest` (use the image you pushed in Step 1).
4.  **Container Disk:** 10 GB (for the OS and app code).
5.  **Volume Disk:** 0 GB (we will use the Network Volume instead).
6.  **Volume Mount Path:** `/workspace/ltx-models`
7.  **Network Volume:** Select the volume created in Step 2.
8.  **Environment Variables:** Add the following:
    - `MODEL_PATH`: `/workspace/ltx-models`
    - `LTX_REPO_PATH`: `/workspace/LTX-Video`
    - `LTX_CONFIG_FILE`: `configs/ltxv-2b-0.9.8-distilled-fp8.yaml`

## 4. Deploy the Serverless Endpoint

1.  Go to the **Serverless Endpoints** section and click **New Endpoint**.
2.  **Endpoint Name:** `ltx-vid-gen-api`
3.  **Select Template:** `LTX-Video-FP8`
4.  **Select GPU:** **A100 (80GB)** or **H100** (Hopper/Ada architecture is required for optimal FP8 kernel performance).
5.  **Active Workers:** Set `0` (for true serverless scaling).
6.  **Max Workers:** Set based on your expected load.
7.  **Idle Timeout:** Set to `60` seconds (workers will stay active for 60s after a job finishes).

## 5. API Usage

Send a POST request to your RunPod Endpoint URL.

### Example Request
```json
{
    "input": {
        "prompt": "A cinematic shot of a sunset over a digital ocean, vibrant purple waves",
        "image_url": "https://example.com/path/to/your/image.jpg",
        "num_frames": 121,
        "num_steps": 30,
        "seed": 42
    }
}
```

### Example Response
The API returns the video as a Base64 string:
```json
{
    "video_base64": "AAAAFGZ0eX..."
}
```