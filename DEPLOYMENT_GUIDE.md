# LTX Video Generation Deployment Guide for RunPod Serverless

This guide provides step-by-step instructions for deploying your `ltx-vid-gen` project on RunPod Serverless, optimized for performance and scalability. It assumes you have a basic understanding of Docker and cloud deployment concepts.

---
## Part 1: Local Setup & Image Preparation

This section covers the tasks you need to perform on your local machine or your GCP VM before deploying to RunPod.

**Prerequisites:**

1.  **RunPod Account**: Sign up for a RunPod account if you haven't already: [https://www.runpod.io/](https://www.runpod.io/)
2.  **Docker Installed**: Ensure Docker is installed and running on your local machine or the GCP VM you're using to build the image. You can download it from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).
3.  **GCP Account & `gcloud` SDK**: You need a GCP account. If you don't have the `gcloud` command-line tool installed, follow the official instructions to install it: [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install). After installation, authenticate it by running `gcloud auth login` in your terminal.

**Step 1: Build the Docker Image**

This step creates a lightweight Docker image containing only your project's code and dependencies. The large model weights will *not* be included in this image.

*   **Open your terminal or command prompt.**
*   **Navigate to your project directory**:
    ```bash
    cd /Users/aditya/Documents/Coding Projects/ltx-vid-gen
    ```
*   **Build the Docker image**: Use the `Dockerfile` provided in your project.
    ```bash
    docker build -t my-ltx-vid-gen-image:latest .
    ```
    *   `my-ltx-vid-gen-image:latest` is a placeholder for your image name and tag. You can choose any name you like.
    *   The `.` at the end specifies that the build context is the current directory.

**Step 2: Push the Docker Image to GCP Artifact Registry (GAR)**

This option is recommended for seamless integration with GCP VMs and allows RunPod to pull your image efficiently.

1.  **Set Your GCP Project ID**: Replace `YOUR_GCP_PROJECT_ID` with your actual GCP project ID.
    ```bash
    export GCP_PROJECT_ID=YOUR_GCP_PROJECT_ID
    ```

2.  **Choose a Region**: Select a GCP region. For example, `us-central1`. This should ideally be close to your RunPod deployment region.
    ```bash
    export GCP_REGION=us-central1
    ```

3.  **Create a Docker Repository in GAR**: If you don't have a GAR repository for Docker images, create one. Replace `ltx-vid-gen-repo` with your desired repository name.
    ```bash
    gcloud artifacts repositories create ltx-vid-gen-repo \
      --repository-format=docker \
      --location=$GCP_REGION \
      --description="Docker repository for LTX Video Generation"
    ```

4.  **Create a Service Account for RunPod**: This account will be used by RunPod to pull images from GAR.
    ```bash
    gcloud iam service-accounts create runpod-docker-puller \
      --display-name "RunPod Docker Puller Service Account"
    ```

5.  **Grant the Service Account Artifact Registry Reader Role**: This permission allows the service account to pull images.
    ```bash
    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
      --member "serviceAccount:runpod-docker-puller@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
      --role "roles/artifactregistry.reader"
    ```

6.  **Generate a Service Account Key**: This JSON key file will be used by RunPod to authenticate. **Keep this file secure.**
    ```bash
    gcloud iam service-accounts keys create ./gcp-service-account-key.json \
      --service-account runpod-docker-puller@$GCP_PROJECT_ID.iam.gserviceaccount.com
    ```
    *   This command saves the key to a file named `gcp-service-account-key.json` in your current directory.

7.  **Authenticate Docker with GAR**: 
    ```bash
    gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
    ```
    *   Replace `$GCP_REGION` with the region you chose earlier.

8.  **Tag Your Docker Image for GAR**: Replace `v1.0.0` with your desired version tag.
    ```bash
    docker tag my-ltx-vid-gen-image:latest $GCP_REGION-docker.pkg.dev/$GCP_PROJECT_ID/ltx-vid-gen-repo/ltx-vid-gen:v1.0.0
    ```

9.  **Push the Tagged Image to GAR**: 
    ```bash
    docker push $GCP_REGION-docker.pkg.dev/$GCP_PROJECT_ID/ltx-vid-gen-repo/ltx-vid-gen:v1.0.0
    ```

*   **Option B: Other Container Registries (e.g., Docker Hub)**
    1.  **Tag your image**: Replace `your-registry-username` with your username or registry path.
        ```bash
        docker tag my-ltx-vid-gen-image:latest your-registry-username/ltx-vid-gen:latest
        ```
    2.  **Log in to your registry**: If you're not already logged in, use your registry's command-line tool (e.g., `docker login`).
    3.  **Push the tagged image**:
        ```bash
        docker push your-registry-username/ltx-vid-gen:latest
        ```

---
## Part 2: RunPod Deployment

This section guides you through deploying your application on RunPod Serverless.

**Step 3: Create a RunPod Network Volume for Model Weights**

This volume will store your LTX model weights, making them accessible to your serverless endpoint without needing to be part of the Docker image.

1.  **Log in to your RunPod Account**.
2.  Navigate to **Network Volumes** from the left-hand menu.
3.  Click the **+ Create** button (or **New Volume**).
4.  **Data Center**: Select a specific Data Center (e.g., `US-NJ`, `EU-RO`). **Crucial:** You must remember this location. Your temporary Pod and Serverless Endpoint **MUST** be deployed in this same Data Center to access the volume.
5.  **Name**: Give it a descriptive name, such as `ltx-models-volume`.
6.  **Size**: Choose a size that can accommodate your model weights. **50GB** is a good starting point.
7.  Click **Create**.

**Step 4: Transfer Model Weights to the Network Volume**

You need to copy your LTX model weights to the RunPod Network Volume you just created. This is typically done by spinning up a temporary RunPod Pod.

1.  **Spin up a temporary RunPod Pod**:
    *   Go to **Pods** > **Deploy** (GPU Pods).
    *   **Select Data Center**: Choose the **exact same Data Center** where you created your Network Volume in Step 3.
    *   **Select a GPU**: Choose any available GPU (e.g., NVIDIA A4000 or similar). Since this is just for file transfer, you don't strictly need an A100, but a faster network helps.
    *   **Customize Deployment**:
        *   **Volume Mount**: Click to expand/add.
        *   **Network Volume**: Select `ltx-models-volume`.
        *   **Mount Path**: Set this to `/workspace/ltx-models`. **This is CRITICAL.**
        *   **Image**: Use a basic image like `runpod/base:0.4.0-cuda12.1.0` or just `ubuntu`.
    *   Click **Deploy**.
2.  **Connect to the Pod via SSH**:
    *   Once the Pod is "Running", click **Connect** to find the SSH command.
    *   Use an SSH client (terminal/PuTTY) to connect:
        ```bash
        ssh root@<POD_IP> -p <PORT> -i <YOUR_PRIVATE_KEY>
        ```
        *(Or use the Web Terminal if SSH is difficult, though SCP requires SSH).*
3.  **Transfer Files**: From your local machine (or wherever weights are), use `scp` to copy weights to the pod.
    ```bash
    scp -P <PORT> -r /path/to/local/weights/* root@<POD_IP>:/workspace/ltx-models/
    ```
    *   Replace `<PORT>`, `<POD_IP>`, and local path.
    *   **Verify**: run `ls /workspace/ltx-models/` inside the pod to ensure files are there.
4.  **Terminate the Temporary Pod**: Once confirmed, **Terminate** (delete) the pod to stop billing. The Network Volume persists.

**Step 5: Deploy Your Serverless Endpoint**

1.  **Navigate to Serverless** from the left-hand menu.
2.  Click **+ New Endpoint**.
3.  **Basic Information**:
    *   **Endpoint Name**: e.g., `ltx-video-gen`.
    *   **Select Data Center**: **Must match** your Network Volume's location.
4.  **Model Configuration (The Template)**:
    *   **Image Name**: Enter your Docker Hub image (e.g., `your-username/ltx-vid-gen-lite:v1.0.0`).
    *   **Container Disk**: Increase to **20GB** (or more) to ensure space for temporary processing.
    *   **Dockerfile Command**: Leave blank (uses the `CMD` from your Dockerfile).
5.  **Compute Configuration**:
    *   **GPU Type**: Select **NVIDIA A100 80GB** (recommended for LTX 13B).
    *   **Min Workers**: 0 (for scale-to-zero) or 1 (for warm start).
    *   **Max Workers**: Set limit (e.g., 3).
    *   **Idle Timeout**: **300** seconds (crucial for long video generation).
    *   **FlashBoot**: Enable if available.
6.  **Advanced / Storage**:
    *   **Network Volume**: Select `ltx-models-volume`.
    *   **Mount Path**: Enter `/workspace/ltx-models`.
7.  **Environment Variables** (Optional):
    *   Add any env vars needed by your code (e.g., bucket names, tokens).
8.  **Deploy**: Click **Create Endpoint**.

**Step 6: Test Your Deployed Endpoint**

Once your endpoint is deployed and shows a "Healthy" status, you can start sending requests to it.

1.  **Find Your Endpoint URL**: In the Serverless section on RunPod, locate your deployed endpoint. It will have a public URL, usually in the format `https://<endpoint-name>-<random-id>.runpod.dev`.
2.  **Send a Request**: You can use `curl` in your terminal, Postman, or a Python script.

    **Example using `curl`**:
    ```bash
    curl -X POST \
      <YOUR_ENDPOINT_URL> \
      -H 'Content-Type: application/json' \
      -d 
        "input": {
          "prompt": "A serene landscape with a flowing river and mountains in the background", 
          "image_url": "https://runpod.io/static/media/runpod-logo.203a9820.svg" 
        }
      }
    ```
    *   Replace `<YOUR_ENDPOINT_URL>` with the actual URL of your deployed endpoint.
    *   Modify the `prompt` and `image_url` to your desired values. The `image_url` must point to a publicly accessible image.

---
## Troubleshooting Common Issues

*   **Cold Start Latency**: If your endpoint takes too long to respond to the first request, ensure FlashBoot is enabled and that you have selected a powerful GPU with sufficient VRAM. Verify the model loading logic in `handler.py` is correct.
*   **Job Timeouts**: If your generation jobs are being cut off before completion, you need to increase the **Timeout (Seconds)** setting in your serverless endpoint configuration (e.g., to 300s or more).
*   **Out of Memory Errors (CUDA OOM)**: This usually indicates the GPU doesn't have enough VRAM for the model. Double-check that you are using an A100 80GB or H100.
*   **Model Not Found Errors**: If you see errors like "No such file or directory" for your model path, verify that the Network Volume is correctly attached in the serverless endpoint configuration and that the Mount Path is exactly `/workspace/ltx-models`. Also, confirm that the weights were successfully transferred to that path on the volume.
*   **General Errors**: Check the **Logs** section for your serverless endpoint on RunPod. This is the most important place to find detailed error messages and diagnose issues.