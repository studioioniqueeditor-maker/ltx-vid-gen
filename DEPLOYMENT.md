# LTX Video I2V - Complete Deployment Guide

This guide provides step-by-step instructions for deploying the LTX Video I2V system to RunPod Serverless with Oracle Cloud integration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Oracle Cloud Setup](#oracle-cloud-setup)
3. [Local Configuration](#local-configuration)
4. [GitHub Repository Setup](#github-repository-setup)
5. [RunPod Configuration](#runpod-configuration)
6. [Testing & Verification](#testing--verification)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts

- [ ] **Oracle Cloud Account** (Free Tier is sufficient)
- [ ] **RunPod Account** (Serverless GPU access)
- [ ] **GitHub Account** (for CI/CD)

### Local Requirements

- [ ] Python 3.11+
- [ ] Docker (optional, for local testing)
- [ ] Git
- [ ] Oracle Cloud CLI (optional)

---

## Oracle Cloud Setup

### Step 1: Create Object Storage Bucket

1. Log in to Oracle Cloud Console
2. Navigate to **Storage → Buckets**
3. Click **Create Bucket**
4. Settings:
   - **Name:** `ltx-video-outputs`
   - **Default Storage Tier:** Standard
   - **Encryption:** Encrypt using Oracle-managed keys
   - **Emit Object Events:** No
   - **Uncommitted Multipart Uploads:** Enable auto cleanup
5. Click **Create**

**Configure Lifecycle Policy:**
1. Click on the bucket name
2. Go to **Lifecycle Policy Rules**
3. Click **Create Rule**
4. Settings:
   - **Name:** `auto-delete-old-videos`
   - **Target:** Objects
   - **Filter:** Prefix: `videos/`
   - **Action:** Delete
   - **Days:** 30
5. Click **Create**

### Step 2: Generate API Keys

1. Navigate to **Identity → Users**
2. Click on your username
3. Scroll to **API Keys**
4. Click **Add API Key**
5. Choose **Generate API Key Pair**
6. Click **Download Private Key** (save as `oci_api_key.pem`)
7. Click **Add**
8. **Copy the configuration preview** - you'll need:
   - User OCID
   - Fingerprint
   - Tenancy OCID
   - Region

### Step 3: Set Up Database

**Option A: Autonomous Database (Free Tier)**

1. Navigate to **Oracle Database → Autonomous Database**
2. Click **Create Autonomous Database**
3. Settings:
   - **Display name:** `ltx-video-db`
   - **Workload type:** Transaction Processing
   - **Deployment type:** Shared Infrastructure
   - **Always Free:** Enable
   - **Database version:** 19c or 23ai
   - **OCPU count:** 1 (Always Free limit)
   - **Storage:** 20 GB (Always Free limit)
4. Set **ADMIN password** (save securely)
5. Click **Create Autonomous Database**

**Option B: MySQL (If preferred)**
1. Navigate to **Databases → MySQL**
2. Click **Create DB System**
3. Follow similar steps for configuration

### Step 4: Create Database Schema

**Connect to Database:**
```bash
# Using SQL*Plus (if installed locally)
sqlplus ADMIN/your-password@your-connection-string

# Or use Oracle Cloud Console SQL Developer Web:
# Database Details → Tools → SQL Developer Web
```

**Run Schema:**
```sql
-- Copy and paste contents of schema.sql
@schema.sql

-- Verify tables created
SELECT table_name FROM user_tables;
```

### Step 5: Insert API Keys

```sql
-- Generate API key hash
-- Python: hashlib.sha256(b"your-api-key-here").hexdigest()

INSERT INTO api_keys (key_hash, key_name, rate_limit_per_minute, is_active)
VALUES (
    'YOUR_SHA256_HASH_HERE',
    'Production API Key 1',
    10,
    'Y'
);

COMMIT;

-- Verify
SELECT key_name, created_at, is_active FROM api_keys;
```

### Step 6: Get Connection Details

**Connection String Format:**
```
(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=hostname)(PORT=1522))(CONNECT_DATA=(SERVICE_NAME=service_name)))
```

**Where to find:**
1. Go to your database
2. Click **DB Connection**
3. Copy the connection string for **TP** (Transaction Processing)

---

## Local Configuration

### Step 1: Configure Environment

```bash
cd /Users/aditya/Documents/Coding\ Projects/ltx-vid-gen

# Copy environment template
cp .env.example .env
```

### Step 2: Fill in .env File

```bash
# Edit .env with your favorite editor
nano .env
# or
code .env
```

**Fill in all values:**

```env
# API Configuration
API_KEYS=your-generated-api-key-1,your-generated-api-key-2

# CORS (your Oracle Cloud app URL)
ALLOWED_ORIGINS=https://your-oracle-app.oraclecloud.com

# Oracle Object Storage
OCI_NAMESPACE=your_namespace
OCI_BUCKET_NAME=ltx-video-outputs
OCI_REGION=us-ashburn-1
OCI_USER_OCID=ocid1.user.oc1..aaaaaa...
OCI_FINGERPRINT=aa:bb:cc:dd:ee:ff:gg:hh:ii:jj:kk:ll:mm:nn:oo:pp
OCI_TENANCY_OCID=ocid1.tenancy.oc1..aaaaaa...
OCI_PRIVATE_KEY=REMOVED
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
REMOVED

# Oracle Database
ORACLE_DB_USER=ADMIN
ORACLE_DB_PASSWORD=your-admin-password
ORACLE_DB_DSN=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=...

# Webhook Secret (generate with: python -c "import secrets; print(secrets.token_hex(32))")
WEBHOOK_SECRET=your-random-hex-string-64-chars
```

### Step 3: Generate Secure Keys

```bash
# Generate API keys
python3 -c "import secrets; [print(f'Key {i+1}: {secrets.token_urlsafe(32)}') for i in range(3)]"

# Generate webhook secret
python3 -c "import secrets; print(f'Webhook Secret: {secrets.token_hex(32)}')"

# Generate API key hashes for database
python3 -c "import hashlib; key='your-api-key-here'; print(hashlib.sha256(key.encode()).hexdigest())"
```

### Step 4: Validate Configuration

```bash
# Test config loading
python3 -c "from config import settings; print(f'✓ Config loaded: {settings.OCI_BUCKET_NAME}')"

# Test database connection
python3 database.py

# Test storage connection
python3 storage.py
```

---

## GitHub Repository Setup

### Step 1: Initialize Git

```bash
# Initialize repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Secure LTX Video I2V deployment

- Implemented 10 critical security fixes
- Added Oracle Cloud integration
- Created RunPod serverless handler
- Set up CI/CD pipeline"
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Settings:
   - **Repository name:** `ltx-vid-gen`
   - **Visibility:** Private (recommended)
   - **Initialize:** Don't initialize (we have local files)
3. Click **Create repository**

### Step 3: Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/ltx-vid-gen.git

# Verify .env is NOT included
git status

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Configure GitHub Secrets

1. Go to repository **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add:
   - Name: `RUNPOD_API_KEY`
   - Value: Your RunPod API key (optional, for automated deployment)

---

## RunPod Configuration

### Step 1: Create RunPod Account

1. Sign up at https://www.runpod.io/
2. Verify email
3. Add payment method
4. Set spending limit (recommended: $100/month for testing)

### Step 2: Build Docker Image

**Automatic (via GitHub Actions):**
```bash
# Create a release to trigger build
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will build and push to ghcr.io
# Monitor progress: https://github.com/YOUR_USERNAME/ltx-vid-gen/actions
```

**Manual (local build):**
```bash
# Build image (takes 20-30 minutes)
docker build -t ltx-video-i2v:latest .

# Tag for GitHub Container Registry
docker tag ltx-video-i2v:latest ghcr.io/YOUR_USERNAME/ltx-vid-gen/ltx-video-i2v:latest

# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Push image
docker push ghcr.io/YOUR_USERNAME/ltx-vid-gen/ltx-video-i2v:latest
```

### Step 3: Create Serverless Endpoint

1. Log in to RunPod Console
2. Navigate to **Serverless**
3. Click **+ New Endpoint**

**Configuration:**

**Basic Settings:**
- **Endpoint Name:** `ltx-video-i2v-production`
- **GPUs:** NVIDIA A40 (48GB VRAM)
- **Workers:**
  - **Active Workers:** 0 (for cost savings)
  - **Max Workers:** 10 (adjust based on expected load)
  - **Idle Timeout:** 5 seconds
- **FlashBoot:** Enabled ✅

**Container Configuration:**
- **Container Image:** `ghcr.io/YOUR_USERNAME/ltx-vid-gen/ltx-video-i2v:latest`
- **Container Disk:** 50 GB
- **Network Volume:** None (model in container)

**Environment Variables:**

Click **+ Environment Variable** for each:

```
API_KEYS = your-api-key-1,your-api-key-2
ALLOWED_ORIGINS = https://your-oracle-app.oraclecloud.com
OCI_NAMESPACE = your_namespace
OCI_BUCKET_NAME = ltx-video-outputs
OCI_REGION = us-ashburn-1
OCI_USER_OCID = ocid1.user...
OCI_FINGERPRINT = aa:bb:cc...
OCI_TENANCY_OCID = ocid1.tenancy...
OCI_PRIVATE_KEY = REMOVED...
ORACLE_DB_USER = ADMIN
ORACLE_DB_PASSWORD = your-password
ORACLE_DB_DSN = (DESCRIPTION=...
WEBHOOK_SECRET = your-webhook-secret
```

**Advanced Settings:**
- **Max Execution Time:** 300 seconds (5 minutes)
- **Request Timeout:** 600 seconds (10 minutes)

4. Click **Deploy**
5. **Copy the Endpoint ID** (you'll need this for API calls)

### Step 4: Test Endpoint

```bash
# Get endpoint URL
ENDPOINT_ID="your-endpoint-id"
API_KEY="your-api-key"

# Submit test job
curl -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/run" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "input": {
      "job_id": "test-'$(uuidgen)'",
      "api_key_hash": "'$(echo -n $API_KEY | sha256sum | cut -d' ' -f1)'",
      "image_url": "https://picsum.photos/1280/720",
      "prompt": "Slow zoom in with subtle camera movement",
      "seed": 42,
      "width": 1280,
      "height": 720,
      "num_frames": 121
    }
  }'
```

---

## Testing & Verification

### Step 1: Test Database Connection

```python
import asyncio
from database import db

async def test():
    db.init_pool()
    async with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 'Connected!' FROM DUAL")
        print(cursor.fetchone()[0])
    db.close()

asyncio.run(test())
```

### Step 2: Test Storage Upload

```python
import asyncio
from storage import storage

async def test():
    # Create dummy file
    with open('/tmp/test.mp4', 'wb') as f:
        f.write(b'test video content')

    # Upload
    obj_name, url = await storage.upload_video('/tmp/test.mp4', 'test-job-123')
    print(f"✓ Uploaded: {obj_name}")
    print(f"✓ URL: {url}")

asyncio.run(test())
```

### Step 3: Test End-to-End

```python
import requests
import hashlib
import uuid

API_KEY = "your-api-key"
ENDPOINT = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run"

# Submit job
job_id = str(uuid.uuid4())
api_key_hash = hashlib.sha256(API_KEY.encode()).hexdigest()

response = requests.post(
    ENDPOINT,
    headers={"X-API-Key": API_KEY},
    json={
        "input": {
            "job_id": job_id,
            "api_key_hash": api_key_hash,
            "image_url": "https://picsum.photos/1280/720",
            "prompt": "Camera slowly zooms in, subtle motion",
            "seed": 42
        }
    }
)

print(f"Job submitted: {response.json()}")
print(f"Job ID: {job_id}")

# Check database
# SELECT * FROM video_jobs WHERE job_id = 'your-job-id';
```

---

## Monitoring & Maintenance

### Daily Checks

1. **RunPod Dashboard**
   - Check active workers
   - Monitor costs
   - Review error rates

2. **Database Queries**
   ```sql
   -- Today's statistics
   SELECT status, COUNT(*)
   FROM video_jobs
   WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1' DAY
   GROUP BY status;

   -- Failed jobs
   SELECT job_id, error_message
   FROM video_jobs
   WHERE status = 'failed'
   AND created_at > CURRENT_TIMESTAMP - INTERVAL '1' DAY;
   ```

3. **Storage Usage**
   ```sql
   -- Check Oracle Cloud Storage dashboard
   -- Monitor: Total size, Number of objects
   ```

### Weekly Maintenance

```sql
-- Clean up old rate limits
EXEC cleanup_rate_limits(1);

-- Review API key usage
SELECT key_name, total_requests, last_used_at
FROM api_keys
WHERE is_active = 'Y';
```

### Monthly Tasks

- Review and rotate API keys
- Update dependencies
- Check for model updates
- Review costs and optimize

---

## Troubleshooting

### Issue: "Database connection failed"

```bash
# Test connection string
echo "exit" | sqlplus ADMIN/password@'(DESCRIPTION=...'

# Check network access
ping your-db-hostname

# Verify credentials
# Check ORACLE_DB_USER, ORACLE_DB_PASSWORD
```

### Issue: "Failed to upload to Object Storage"

```bash
# Verify bucket exists
oci os bucket get --bucket-name ltx-video-outputs

# Check credentials
oci os ns get

# Test API key
# Regenerate if needed
```

### Issue: "Webhook not delivered"

```sql
-- Check webhook attempts
SELECT job_id, webhook_url, webhook_attempts, last_webhook_attempt
FROM video_jobs
WHERE webhook_delivered = 'N'
AND webhook_url IS NOT NULL;
```

```bash
# Test webhook endpoint manually
curl -X POST https://your-app.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

### Issue: "GPU out of memory"

Reduce parameters:
- Width/Height: Try 960x540 instead of 1280x720
- Num frames: Try 81 instead of 121
- Check if multiple jobs running simultaneously

### Issue: "Cold start too slow"

- Verify model weights are in container (check Dockerfile)
- Increase active workers to 1
- Check RunPod region (choose closest to your users)

---

## Cost Optimization Tips

1. **Use 0 active workers** during off-peak hours
2. **Set aggressive lifecycle policies** on Object Storage (30 days)
3. **Clean up rate limit logs** hourly
4. **Archive old job records** after 90 days
5. **Monitor and set spending alerts** on RunPod
6. **Use FlashBoot** for faster cold starts (included free)

---

## Next Steps

After deployment:

1. ✅ Set up monitoring alerts
2. ✅ Create backup schedule for database
3. ✅ Document your Oracle Cloud app integration
4. ✅ Test failure scenarios
5. ✅ Set up log aggregation (optional)
6. ✅ Configure automated testing (optional)

---

## Support Resources

- **RunPod Docs:** https://docs.runpod.io/
- **Oracle Cloud Docs:** https://docs.oracle.com/
- **LTX Video:** https://github.com/Lightricks/LTX-Video
- **This Project:** Check README.md and code comments

---

**Deployment complete! 🎉**
