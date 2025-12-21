# Deployment Guide: LTX Video Generation (RunPod Serverless)

This guide details how to deploy the rebuilt LTX Video Generation service on RunPod Serverless using the 2B distilled FP8 model.

## 1. Network Volume Setup
To avoid high latency and cold start delays, models should be stored on a RunPod Network Volume.

1.  Create a **Network Volume** in your RunPod dashboard (e.g., in the same region where you plan to deploy your GPU).
2.  Mount this volume to a temporary GPU pod to populate it.
3.  Inside the pod, run the `download_models.py` script:
    ```bash
    export MODEL_PATH="/workspace/ltx-models"
    python3 download_models.py
    ```
4.  Verify the download:
    ```bash
    python3 verify_models.py
    ```

## 2. RunPod Template Configuration
Create a new Serverless Template with the following settings:

*   **Container Image:** Your Docker Hub image (e.g., `your-username/ltx-vid-gen:latest`).
*   **Container Disk:** 10 GB.
*   **Volume Disk:** 0 GB (since we use a Network Volume).
*   **Volume Mount Path:** `/workspace/ltx-models`.
*   **Network Volume:** Select the volume created in Step 1.

### Environment Variables
*   `MODEL_PATH`: `/workspace/ltx-models`
*   `LTX_REPO_PATH`: `/workspace/LTX-Video`
*   `LTX_CONFIG_FILE`: `configs/ltxv-2b-0.9.8-distilled-fp8.yaml`

## 3. Serverless Endpoint
1.  Deploy a new **Serverless Endpoint** using the template created above.
2.  Select the **A100 (80GB)** or **H100** GPU for optimal performance with FP8.
3.  Set the **Idle Timeout** (e.g., 60 seconds) and **Max Workers** as needed.

## 4. API Usage
Send a POST request to your endpoint:

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

The response will contain the video encoded in Base64:
```json
{
    "video_base64": "..."
}
```
