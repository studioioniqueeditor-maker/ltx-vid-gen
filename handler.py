"""
RunPod Serverless Handler
Entry point for LTX Video I2V generation on RunPod
"""

import runpod
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Any

from generate_i2v import load_pipeline, generate_video
from storage import OracleObjectStorage
from database import OracleDatabase
from webhooks import WebhookDelivery
from validation import validate_generation_params
from utils import sanitize_error_message, format_duration
from config import settings

# ==========================================
# Global Services (loaded once on cold start)
# ==========================================
pipe = None
storage = None
db = None
webhook_delivery = None


def init_services():
    """
    Initialize services on cold start
    This runs once when the worker starts
    """
    global pipe, storage, db, webhook_delivery

    print("=" * 60)
    print("🚀 Initializing LTX Video I2V Handler")
    print("=" * 60)

    # Load model pipeline
    if pipe is None:
        print("\n[1/4] Loading LTX Video pipeline...")
        start = time.time()
        pipe = load_pipeline()
        elapsed = time.time() - start
        print(f"✓ Pipeline loaded in {format_duration(elapsed)}")

    # Initialize Oracle Object Storage
    if storage is None:
        print("\n[2/4] Initializing Oracle Object Storage...")
        storage = OracleObjectStorage()
        print(f"✓ Storage ready (bucket: {storage.bucket_name})")

    # Initialize Oracle Database
    if db is None:
        print("\n[3/4] Initializing Oracle Database...")
        db = OracleDatabase()
        db.init_pool(min_connections=2, max_connections=5)
        print("✓ Database pool initialized")

    # Initialize webhook delivery
    if webhook_delivery is None:
        print("\n[4/4] Initializing webhook delivery...")
        webhook_delivery = WebhookDelivery(db)
        print("✓ Webhook delivery ready")

    print("\n" + "=" * 60)
    print("✅ Handler initialization complete")
    print("=" * 60 + "\n")


async def process_job(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process video generation job

    Expected input format:
    {
        "job_id": "uuid",
        "api_key_hash": "sha256_hash",
        "image_url": "https://...",
        "prompt": "motion description",
        "seed": 42,
        "width": 1280,
        "height": 720,
        "num_frames": 121,
        "webhook_url": "https://your-app.com/webhook" (optional)
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
    api_key_hash = job_input.get('api_key_hash')
    webhook_url = job_input.get('webhook_url')

    print(f"\n{'='*60}")
    print(f"📹 Processing job: {job_id}")
    print(f"{'='*60}")

    try:
        # Validate all input parameters
        print("\n[1/5] Validating parameters...")
        validated = validate_generation_params(
            image_url=job_input.get('image_url'),
            prompt=job_input.get('prompt'),
            width=job_input.get('width'),
            height=job_input.get('height'),
            num_frames=job_input.get('num_frames'),
            num_steps=job_input.get('num_steps'),
            seed=job_input.get('seed'),
            webhook_url=webhook_url
        )
        print(f"✓ Parameters validated")
        print(f"  - Image: {validated['image_url'][:50]}...")
        print(f"  - Prompt: {validated['prompt'][:50]}...")
        print(f"  - Resolution: {validated['width']}x{validated['height']}")
        print(f"  - Frames: {validated['num_frames']}")

        # Update job status to 'processing'
        print("\n[2/5] Updating job status...")
        await db.update_job_status(
            job_id=job_id,
            status='processing',
            started_at=datetime.utcnow()
        )
        print("✓ Job status: processing")

        # Generate video
        print("\n[3/5] Generating video...")
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
        print("\n[4/5] Uploading to Oracle Cloud Storage...")
        upload_start = time.time()

        object_name, signed_url = await storage.upload_video(
            file_path=video_path,
            job_id=job_id
        )

        upload_time = time.time() - upload_start
        print(f"✓ Upload complete in {format_duration(upload_time)}")
        print(f"  - Object: {object_name}")
        print(f"  - URL: {signed_url[:60]}...")

        # Update database with success
        print("\n[5/5] Finalizing...")
        await db.complete_job(
            job_id=job_id,
            video_url=signed_url,
            object_name=object_name,
            generation_time=generation_time
        )
        print("✓ Database updated")

        # Clean up local file
        if os.path.exists(video_path):
            os.remove(video_path)
            print("✓ Local file cleaned up")

        # Send webhook if configured
        if webhook_url:
            print("\n📤 Sending webhook...")
            webhook_success = await webhook_delivery.send_completion_webhook(job_id)
            if webhook_success:
                print("✓ Webhook delivered successfully")
            else:
                print("⚠️  Webhook delivery failed (will retry)")

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

        # Update database with failure
        try:
            await db.fail_job(job_id, str(e))
            print("✓ Database updated with error status")
        except Exception as db_error:
            print(f"⚠️  Failed to update database: {db_error}")

        # Send failure webhook if configured
        if webhook_url:
            try:
                print("📤 Sending failure webhook...")
                await webhook_delivery.send_completion_webhook(job_id)
                print("✓ Failure webhook sent")
            except Exception as webhook_error:
                print(f"⚠️  Webhook delivery failed: {webhook_error}")

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
