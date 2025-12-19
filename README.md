# LTX Video Generation (RunPod Serverless)

This project provides a service for generating videos from text prompts and an initial image using the LTX model. It is optimized for RunPod Serverless with "lite" Docker images and network volume storage.

## Features

*   Video generation from text prompts and an initial image.
*   Supports FP8 quantized models for faster inference on A100.
*   Returns generated video directly as Base64 encoded string.
*   Zero external storage dependencies (removed OCI).

## Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## API Usage

Send POST requests to your RunPod Serverless endpoint.

### Request Format

```json
{
    "input": {
        "prompt": "A futuristic cityscape at sunset",
        "image_url": "https://example.com/path/to/your/image.jpg",
        "width": 1280,
        "height": 720,
        "num_frames": 121,
        "num_steps": 8,
        "seed": 42
    }
}
```

### Response Format

The API returns the video file encoded in Base64.

```json
{
    "video_base64": "AAAAFGZ0eX..."
}
```

### Environment Variables

No external API keys are required for the core functionality.
*   `MODEL_PATH`: Defaults to `/workspace/ltx-models`