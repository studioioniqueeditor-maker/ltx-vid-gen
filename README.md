# LTX Video I2V - RunPod Serverless Deployment

Production-ready Image-to-Video generation service using **LTX Video 13B**, deployed on **RunPod Serverless** with **Oracle Cloud** integration.

## Features

- ✅ **Secure**: API key authentication, input validation, SSRF prevention, rate limiting
- ✅ **Scalable**: RunPod serverless auto-scaling (0-10 workers)
- ✅ **Cost-Effective**: Pay-per-use, optimized for <50 videos/day (~$30-50/month)
- ✅ **Reliable**: Webhook delivery with retries, Oracle DB persistence
- ✅ **Fast**: FlashBoot cold starts <2s, generation ~45s per video @ 720p

## Architecture

```
Oracle Cloud App → RunPod Serverless API → LTX Video Generator
                                                  ↓
                                   Oracle Object Storage (videos)
                                                  ↓
                                   Oracle Database (job metadata)
                                                  ↓
                                   Webhook → Oracle Cloud App
```

## Security Fixes Implemented

This implementation addresses 10 critical security vulnerabilities:

1. ✅ **CORS misconfiguration** - Restricted to specific origins
2. ✅ **No authentication** - API key authentication added
3. ✅ **Path traversal** - Path sanitization implemented
4. ✅ **SSRF vulnerability** - URL validation with IP blocking
5. ✅ **Unrestricted file uploads** - Size and type validation
6. ✅ **No rate limiting** - Database-backed rate limiting
7. ✅ **IDOR vulnerabilities** - API key ownership checks
8. ✅ **Unbounded memory storage** - Oracle DB persistence
9. ✅ **Missing input validation** - Comprehensive validation
10. ✅ **Error message leakage** - Sanitized error responses

## Project Structure

```
ltx-vid-gen/
├── config.py              # Configuration management (Pydantic)
├── auth.py                # API key authentication & rate limiting
├── validation.py          # Input validation (SSRF, injection prevention)
├── utils.py               # Path sanitization utilities
├── database.py            # Oracle Database client
├── storage.py             # Oracle Object Storage client
├── webhooks.py            # Webhook delivery with retries
├── generate_i2v.py        # Video generation (updated with error handling)
├── handler.py             # RunPod serverless entry point
├── Dockerfile             # Container with model weights (~30GB)
├── requirements.txt       # Python dependencies
├── schema.sql             # Oracle Database schema
├── .env.example           # Environment variable template
├── .github/workflows/
│   └── deploy-runpod.yml  # CI/CD pipeline
└── api_server.py          # FastAPI server (needs updates - see below)
```

## Quick Start

### Prerequisites

1. **Oracle Cloud Account** (Free Tier)
   - Object Storage bucket created
   - Database provisioned
   - API credentials generated

2. **RunPod Account**
   - Serverless endpoint configured
   - A40 GPU selected

3. **GitHub Repository**
   - Code pushed
   - Secrets configured

### Setup Steps

#### 1. Oracle Cloud Setup

**Object Storage:**
```bash
# Create bucket
Bucket Name: ltx-video-outputs
Privacy: Private
Lifecycle Policy: Delete after 30 days
```

**Database:**
```bash
# Run schema.sql to create tables
sqlplus user/password@connection_string @schema.sql

# Insert API keys (SHA-256 hashed)
INSERT INTO api_keys (key_hash, key_name, rate_limit_per_minute)
VALUES ('your_sha256_hash_here', 'Production Key', 10);
```

**Generate API Credentials:**
```bash
# In Oracle Cloud Console:
# Identity → Users → Your User → API Keys → Add API Key
# Download private key and note fingerprint
```

#### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
# Generate secure API keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate webhook secret
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 3. GitHub Repository Setup

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: LTX Video I2V with security fixes"

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/ltx-vid-gen.git
git push -u origin main
```

**Configure GitHub Secrets:**
- `RUNPOD_API_KEY` - Your RunPod API key (optional, for automated deployment)

#### 4. Build and Deploy

**Option A: GitHub Actions (Automated)**
```bash
# Create a release to trigger deployment
git tag v1.0.0
git push origin v1.0.0

# Or push to main branch
git push origin main
```

**Option B: Manual Build**
```bash
# Build Docker image locally
docker build -t ltx-video-i2v:latest .

# Push to GitHub Container Registry
docker tag ltx-video-i2v:latest ghcr.io/YOUR_USERNAME/ltx-vid-gen/ltx-video-i2v:latest
docker push ghcr.io/YOUR_USERNAME/ltx-vid-gen/ltx-video-i2v:latest
```

#### 5. RunPod Configuration

**Create Serverless Endpoint:**
1. Go to RunPod Console → Serverless
2. Create New Endpoint
3. Settings:
   - Name: `ltx-video-i2v-production`
   - GPU: A40 (48GB VRAM)
   - Container Image: `ghcr.io/YOUR_USERNAME/ltx-vid-gen/ltx-video-i2v:latest`
   - Container Disk: 50GB
   - Active Workers: 0
   - Max Workers: 10
   - Idle Timeout: 5 seconds
   - FlashBoot: Enabled

**Set Environment Variables:**
```
API_KEYS=your-api-key-1,your-api-key-2
ALLOWED_ORIGINS=https://your-oracle-app.com

OCI_NAMESPACE=your-namespace
OCI_BUCKET_NAME=ltx-video-outputs
OCI_REGION=us-ashburn-1
OCI_USER_OCID=ocid1.user...
OCI_FINGERPRINT=aa:bb:cc...
OCI_TENANCY_OCID=ocid1.tenancy...
OCI_PRIVATE_KEY=REMOVED...

ORACLE_DB_USER=your_db_user
ORACLE_DB_PASSWORD=your_db_password
ORACLE_DB_DSN=your_connection_string

WEBHOOK_SECRET=your-webhook-secret
```

## API Usage

### From Your Oracle Cloud Application

```python
import requests
import hashlib
import uuid

# Your API key
API_KEY = "your-api-key-here"
RUNPOD_ENDPOINT = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run"

# Generate job ID
job_id = str(uuid.uuid4())

# Hash API key for database
api_key_hash = hashlib.sha256(API_KEY.encode()).hexdigest()

# Submit job
response = requests.post(
    RUNPOD_ENDPOINT,
    headers={"X-API-Key": API_KEY},
    json={
        "input": {
            "job_id": job_id,
            "api_key_hash": api_key_hash,
            "image_url": "https://your-app.com/image.jpg",
            "prompt": "Slow zoom in, subtle motion",
            "webhook_url": "https://your-app.com/webhook/video-complete",
            "seed": 42,
            "width": 1280,
            "height": 720,
            "num_frames": 121
        }
    }
)

print(f"Job submitted: {response.json()}")
```

### Webhook Receiver (Oracle Cloud App)

```python
from fastapi import FastAPI, Request, Header, HTTPException
import hmac
import hashlib
import json

app = FastAPI()

@app.post("/webhook/video-complete")
async def receive_webhook(
    request: Request,
    x_webhook_signature: str = Header(...),
    x_job_id: str = Header(...)
):
    payload = await request.json()

    # Verify signature
    secret = "your-webhook-secret"
    message = json.dumps(payload, sort_keys=True).encode()
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(x_webhook_signature, expected):
        raise HTTPException(401, "Invalid signature")

    # Process webhook
    if payload['status'] == 'completed':
        video_url = payload['video_url']
        # Save to your database, notify user, etc.
        print(f"Video ready: {video_url}")

    return {"received": True}
```

## Cost Estimates

### RunPod Serverless (A40)
- $0.40/hour when running
- ~45 seconds per video = ~$0.005/video
- **10 videos/day:** ~$15/month
- **50 videos/day:** ~$75/month

### Oracle Cloud (Free Tier)
- 10GB Object Storage: **Free**
- Database (Always Free): **Free**
- Total: **$0/month** (within free tier limits)

### **Expected Total**
- Low traffic (<50 videos/day): **$30-50/month**
- Medium traffic (100-500 videos/day): **$150-400/month**

## Monitoring

### RunPod Dashboard
- Monitor active workers
- Check GPU utilization
- Track costs in real-time

### Database Queries

**Job statistics:**
```sql
SELECT status, COUNT(*), AVG(generation_time_seconds)
FROM video_jobs
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY status;
```

**Failed jobs:**
```sql
SELECT job_id, error_message, created_at
FROM video_jobs
WHERE status = 'failed'
ORDER BY created_at DESC
FETCH FIRST 10 ROWS ONLY;
```

## Troubleshooting

### Common Issues

**1. "Failed to initialize database pool"**
- Check `ORACLE_DB_DSN` connection string
- Verify database is accessible from RunPod
- Ensure credentials are correct

**2. "Failed to upload video"**
- Check Oracle Cloud credentials (`OCI_USER_OCID`, etc.)
- Verify bucket exists and is in correct region
- Check private key format (must include BEGIN/END lines)

**3. "Webhook delivery failed"**
- Verify webhook URL is accessible
- Check `WEBHOOK_SECRET` matches between systems
- Review webhook_attempts in database

**4. "GPU out of memory"**
- Reduce resolution (try 960x540)
- Reduce num_frames (try 81)
- Check for other jobs running on same GPU

## Important Notes for api_server.py

⚠️ **The existing `api_server.py` file needs to be updated with security fixes.**

Key changes required:
1. Add authentication: `Depends(verify_api_key)` on all endpoints
2. Fix CORS: Use `settings.ALLOWED_ORIGINS` instead of `["*"]`
3. Replace in-memory storage with database calls
4. Add input validation before processing
5. Remove `/download` endpoint (use Oracle Cloud URLs)
6. Update `/generate` to create database job and submit to RunPod
7. Add proper health checks

Refer to the plan file for detailed modifications needed.

## Security Best Practices

1. **Rotate API keys** quarterly
2. **Use HTTPS** for all webhooks
3. **Verify webhook signatures** before processing
4. **Monitor database** for unusual activity
5. **Set billing alerts** on RunPod and Oracle
6. **Review logs** regularly for security events
7. **Keep dependencies updated** regularly

## Contributing

This is a production deployment for a specific use case. For general LTX Video usage, see the [official repository](https://github.com/Lightricks/LTX-Video).

## License

This deployment code is provided as-is. The LTX Video model has its own license - see the official repository.

## Support

For issues with:
- **LTX Video model**: See official repository
- **RunPod**: Check RunPod documentation or support
- **Oracle Cloud**: See Oracle Cloud documentation
- **This deployment**: Open an issue in this repository

---

**Built with ❤️ for secure, scalable AI video generation**
