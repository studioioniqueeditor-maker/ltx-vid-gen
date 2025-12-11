"""
Webhook Delivery System
Reliable webhook delivery with retries and HMAC signatures
"""

import httpx
import asyncio
import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, Optional
from config import settings
from database import OracleDatabase


class WebhookError(Exception):
    """Custom webhook error"""
    pass


class WebhookDelivery:
    """Webhook delivery system with retry logic"""

    def __init__(self, db: OracleDatabase):
        """
        Initialize webhook delivery

        Args:
            db: Database instance for tracking delivery status
        """
        self.db = db
        self.timeout = settings.WEBHOOK_TIMEOUT
        self.max_retries = settings.WEBHOOK_MAX_RETRIES
        self.secret = settings.WEBHOOK_SECRET

    def _generate_signature(self, payload: dict) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload

        Args:
            payload: Webhook payload dictionary

        Returns:
            Hex-encoded HMAC signature
        """
        # Sort keys for consistent signature
        message = json.dumps(payload, sort_keys=True).encode()

        # Generate HMAC
        signature = hmac.new(
            self.secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()

        return signature

    async def deliver_webhook(
        self,
        webhook_url: str,
        payload: dict,
        job_id: str,
        attempt: int = 1
    ) -> bool:
        """
        Deliver webhook with retry logic

        Args:
            webhook_url: URL to POST webhook to
            payload: Webhook payload
            job_id: Job ID for tracking
            attempt: Current attempt number

        Returns:
            True if delivery successful
        """
        if attempt > self.max_retries:
            print(f"✗ Webhook delivery failed after {self.max_retries} attempts for job {job_id}")
            return False

        try:
            # Generate signature
            signature = self._generate_signature(payload)

            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Webhook-Signature': signature,
                'X-Job-ID': job_id,
                'User-Agent': 'LTX-Video-Webhook/1.0'
            }

            print(f"Delivering webhook (attempt {attempt}/{self.max_retries}) to {webhook_url}")

            # Send webhook
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    follow_redirects=True
                )

                # Check response status
                if 200 <= response.status_code < 300:
                    print(f"✓ Webhook delivered successfully for job {job_id} (status: {response.status_code})")

                    # Update database
                    await self.db.update_webhook_delivered(
                        job_id=job_id,
                        delivered=True,
                        attempts=attempt
                    )

                    return True
                else:
                    raise Exception(
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )

        except httpx.TimeoutException:
            error_msg = f"Timeout after {self.timeout}s"
            print(f"✗ Webhook timeout (attempt {attempt}): {error_msg}")

        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            print(f"✗ Webhook request error (attempt {attempt}): {error_msg}")

        except Exception as e:
            error_msg = str(e)
            print(f"✗ Webhook error (attempt {attempt}): {error_msg}")

        # Update attempt count in database
        await self.db.update_webhook_delivered(
            job_id=job_id,
            delivered=False,
            attempts=attempt
        )

        # Retry with exponential backoff
        if attempt < self.max_retries:
            # Backoff: 5s, 10s, 20s for attempts 1, 2, 3
            backoff = (2 ** attempt) * 2.5
            print(f"Retrying webhook in {backoff}s...")
            await asyncio.sleep(backoff)

            return await self.deliver_webhook(
                webhook_url=webhook_url,
                payload=payload,
                job_id=job_id,
                attempt=attempt + 1
            )

        return False

    async def send_completion_webhook(self, job_id: str) -> bool:
        """
        Send webhook for completed or failed job

        Args:
            job_id: Job ID

        Returns:
            True if webhook delivered successfully (or no webhook configured)
        """
        # Fetch job details from database
        job = await self.db.get_job(job_id)

        if not job:
            print(f"✗ Job not found: {job_id}")
            return False

        # Check if webhook URL is configured
        webhook_url = job.get('webhook_url')
        if not webhook_url:
            print(f"No webhook configured for job {job_id}")
            return True  # Not an error - just no webhook

        # Build payload based on job status
        payload = {
            'job_id': job_id,
            'status': job['status'],
            'created_at': job['created_at'],
            'completed_at': job['completed_at'],
        }

        if job['status'] == 'completed':
            # Include video URL and generation time
            payload.update({
                'video_url': job['video_url'],
                'generation_time_seconds': job['generation_time_seconds']
            })

        elif job['status'] == 'failed':
            # Include error message
            payload['error_message'] = job['error_message']

        # Deliver webhook
        return await self.deliver_webhook(
            webhook_url=webhook_url,
            payload=payload,
            job_id=job_id
        )

    async def send_custom_webhook(
        self,
        webhook_url: str,
        payload: dict,
        job_id: str
    ) -> bool:
        """
        Send custom webhook (for testing or special events)

        Args:
            webhook_url: URL to POST to
            payload: Custom payload
            job_id: Job ID for tracking

        Returns:
            True if successful
        """
        return await self.deliver_webhook(
            webhook_url=webhook_url,
            payload=payload,
            job_id=job_id
        )

    @staticmethod
    def verify_webhook_signature(payload: dict, signature: str, secret: str) -> bool:
        """
        Verify webhook signature (for webhook receiver to validate)

        Args:
            payload: Received payload
            signature: Received signature from X-Webhook-Signature header
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        # Generate expected signature
        message = json.dumps(payload, sort_keys=True).encode()
        expected = hmac.new(
            secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(signature, expected)


# Example webhook receiver validation code
"""
# Oracle Cloud App - Webhook Receiver Example

from fastapi import FastAPI, Request, HTTPException, Header

app = FastAPI()

@app.post("/webhook/video-complete")
async def receive_webhook(
    request: Request,
    x_webhook_signature: str = Header(...),
    x_job_id: str = Header(...)
):
    # Get payload
    payload = await request.json()

    # Verify signature
    from webhooks import WebhookDelivery
    secret = "your-webhook-secret"  # Same as in .env

    if not WebhookDelivery.verify_webhook_signature(payload, x_webhook_signature, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook
    job_id = payload['job_id']
    status = payload['status']

    if status == 'completed':
        video_url = payload['video_url']
        # Save video URL to your database, notify user, etc.
        print(f"Video ready: {video_url}")

    elif status == 'failed':
        error = payload.get('error_message', 'Unknown error')
        # Handle failure, notify user, etc.
        print(f"Video generation failed: {error}")

    return {"received": True}
"""


if __name__ == "__main__":
    # Test webhook delivery
    import asyncio
    from database import db

    async def test():
        print("Testing webhook delivery...")

        # Initialize database
        db.init_pool(min_connections=1, max_connections=2)

        # Create webhook delivery instance
        webhook = WebhookDelivery(db)

        # Test payload
        test_payload = {
            'job_id': 'test-job-123',
            'status': 'completed',
            'video_url': 'https://example.com/video.mp4',
            'generation_time_seconds': 45.3
        }

        # Generate signature
        signature = webhook._generate_signature(test_payload)
        print(f"✓ Generated signature: {signature[:16]}...")

        # Verify signature
        is_valid = WebhookDelivery.verify_webhook_signature(
            test_payload,
            signature,
            settings.WEBHOOK_SECRET
        )
        print(f"✓ Signature verification: {is_valid}")

        # Note: Actual webhook delivery requires a valid webhook URL
        # print("\nTo test delivery, update webhook_url and uncomment:")
        # await webhook.deliver_webhook(
        #     webhook_url="https://your-app.com/webhook",
        #     payload=test_payload,
        #     job_id='test-job-123'
        # )

        db.close()

    asyncio.run(test())
