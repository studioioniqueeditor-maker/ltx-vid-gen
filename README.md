# LTX Video Generation (RunPod Serverless)

This project provides a service for generating videos from text prompts and an initial image using the LTX model.

## Features

*   Video generation from text prompts and an initial image.
*   Optimized for deployment on RunPod Serverless.

## Setup for RunPod Serverless

To deploy this project on RunPod Serverless, follow these steps:

1.  **Build the Docker Image**: Use the provided `Dockerfile` to build a lean Docker image. Ensure you are not copying model weights into the image.
    ```bash
    docker build -t your-image-name .
    ```
    If you are using GCP Artifact Registry, follow the RunPod documentation for pushing to and pulling from GAR.

2.  **Prepare Model Weights**: Create a RunPod Network Volume (e.g., 50GB or more, depending on your model size). Transfer your LTX model weights to the `/workspace/ltx-models` directory on this volume.

3.  **Deploy to RunPod Serverless**: 
    *   Create a new Serverless Endpoint on RunPod.
    *   Attach the Network Volume containing your model weights.
    *   Configure the endpoint to use the Docker image you built.
    *   **Crucially, set the endpoint timeout to at least 300 seconds** to accommodate video generation time.
    *   Select an appropriate GPU (e.g., NVIDIA A100 80GB or H100).
    
4.  **Use the API**: Send POST requests to your RunPod Serverless endpoint with a JSON payload, for example:
    ```json
    {
        "input": {
            "prompt": "A futuristic cityscape at sunset",
            "image_url": "https://example.com/path/to/your/image.jpg"
        }
    }
    ```

## Project Structure

*   `config.py`: Configuration settings.
*   `generate_i2v.py`: Core video generation logic (LTX model integration).
*   `handler.py`: The main entry point for the RunPod Serverless handler, responsible for loading the model and processing requests.
*   `storage.py`: Utility for uploading generated videos to cloud storage (e.g., S3/GCS).
*   `utils.py`: General utility functions.
*   `validation.py`: Input validation module.
*   `requirements.txt`: Python dependencies.
*   `Dockerfile`: Instructions for building the Docker image.

## Ignoring Files

Files and directories ignored by git (see `.gitignore`):

*   `oci_private_key.pem`
*   `.env`
*   `_OLD/`
*   `v1/`

## Note on Model Loading

The `handler.py` script is configured to load the LTX model into memory globally upon the first request. This ensures that subsequent requests benefit from the model already being in VRAM, leading to significantly reduced latency.
