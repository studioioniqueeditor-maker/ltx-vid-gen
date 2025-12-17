"""
RunPod Serverless Handler - Simplified
Entry point for LTX Video I2V generation on RunPod
Async with status polling (no webhooks, no database in handler)
"""

import runpod
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any

from generate_i2v import load_pipeline, generate_video
from storage import OracleObjectStorage
from validation import validate_generation_params
from utils import sanitize_error_message, format_duration
from config import settings

# ==========================================
# Global Services (loaded once on cold start)
# ==========================================
pipe = None
storage = None


def init_services():
    """
    Initialize services on cold start
    This runs once when the worker starts
    """
    global pipe, storage

    print("=" * 60)
    print("🚀 Initializing LTX Video I2V Handler")
    print("=" * 60)

    # Load model pipeline
    if pipe is None:
        print("\n[1/2] Loading LTX Video pipeline...")
        start = time.time()
        pipe = load_pipeline()
        elapsed = time.time() - start
        print(f"✓ Pipeline loaded in {format_duration(elapsed)}")

    # Initialize Oracle Object Storage
    if storage is None:
        print("\n[2/2] Initializing Oracle Object Storage...")
        storage = OracleObjectStorage()
        print(f"✓ Storage ready (bucket: {storage.bucket_name})")

    print("\n" + "=" * 60)
    print("✅ Handler initialization complete")
    print("=" * 60 + "\n")


async def process_job(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process video generation job

    Expected input format:
    {
        "job_id": "uuid",
        "image_url": "https://...",
        "prompt": "motion description",
        "seed": 42,
        "width": 1280,
        "height": 720,
        "num_frames": 121
    }

    Returns:
    {
        "status": "completed" | "failed",
        "job_id": "uuid",
        "video_url": "https://..." (if completed),
        "generation_time_seconds": 45.3 (if completed),
        "error": "error message" (if failed)
    }
    """

    # Initialize services if not already done
    init_services()

    # Extract parameters
    job_id = job_input.get('job_id')

    print(f"\n{'='*60}")
    print(f"🔹 Processing job: {job_id}")
    print(f"{'='*60}")

    try:
        # Validate all input parameters
        print("\n[1/4] Validating parameters...")
        validated = validate_generation_params(
            image_url=job_input.get('image_url'),
            prompt=job_input.get('prompt'),
            width=job_input.get('width'),
            height=job_input.get('height'),
            num_frames=job_input.get('num_frames'),
            num_steps=job_input.get('num_steps'),
            seed=job_input.get('seed'),
            webhook_url=None  # Not used in simplified version
        )
        print(f"✓ Parameters validated")
        print(f"  - Image: {validated['image_url'][:50]}...")
        print(f"  - Prompt: {validated['prompt'][:50]}...")
        print(f"  - Resolution: {validated['width']}x{validated['height']}")
        print(f"  - Frames: {validated['num_frames']}")

        # Generate video
        print("\n[2/4] Generating video...")
        print(f"⏱️  Starting generation at {datetime.utcnow().strftime('%H:%M:%S')}")

        start_time = time.time()

        video_path = generate_video(
            pipe=pipe,
            image_path=validated['image_url'],
            prompt=validated['prompt'],
            output_name=job_id,
            seed=validated['seed']
        )

        generation_time = time.time() - start_time

        print(f"✓ Video generated in {format_duration(generation_time)}")
        print(f"  - Local path: {video_path}")

        # Upload to Oracle Cloud Storage
        print("\n[3/4] Uploading to Oracle Cloud Storage...")
        upload_start = time.time()

        object_name, signed_url = await storage.upload_video(
            file_path=video_path,
            job_id=job_id
        )

        upload_time = time.time() - upload_start
        print(f"✓ Upload complete in {format_duration(upload_time)}")
        print(f"  - Object: {object_name}")
        print(f"  - URL: {signed_url[:60]}...")

        # Clean up local file
        print("\n[4/4] Cleaning up...")
        if os.path.exists(video_path):
            os.remove(video_path)
            print("✓ Local file cleaned up")

        # Success response
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ Job completed successfully!")
        print(f"⏱️  Total time: {format_duration(total_time)}")
        print(f"{'='*60}\n")

        return {
            "status": "completed",
            "job_id": job_id,
            "video_url": signed_url,
            "object_name": object_name,
            "generation_time_seconds": round(generation_time, 2),
            "upload_time_seconds": round(upload_time, 2),
            "total_time_seconds": round(total_time, 2)
        }

    except Exception as e:
        # Handle errors
        error_message = sanitize_error_message(e, include_type=True)
        print(f"\n{'='*60}")
        print(f"❌ Job failed: {error_message}")
        print(f"{'='*60}\n")

        # Return error response
        return {
            "status": "failed",
            "job_id": job_id,
            "error": error_message
        }


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler (synchronous wrapper)

    This is the entry point called by RunPod

    Args:
        event: RunPod event dictionary with 'input' key

    Returns:
        Result dictionary
    """
    job_input = event.get('input', {})

    # Validate required fields
    if not job_input.get('job_id'):
        return {
            "status": "failed",
            "error": "Missing required field: job_id"
        }

    if not job_input.get('image_url') or not job_input.get('prompt'):
        return {
            "status": "failed",
            "error": "Missing required fields: image_url and/or prompt"
        }

    # Run async process_job in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(process_job(job_input))
        return result
    finally:
        loop.close()


# ==========================================
# RunPod Serverless Start
# ==========================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting RunPod Serverless Handler")
    print("=" * 60)
    print(f"Model Path: {settings.MODEL_PATH}")
    print(f"Output Dir: {settings.OUTPUT_DIR}")
    print(f"OCI Bucket: {settings.OCI_BUCKET_NAME}")
    print("=" * 60 + "\n")

    # Start RunPod serverless
    runpod.serverless.start({"handler": handler})
