"""
FastAPI Server for LTX Video I2V
REST API for remote video generation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import time
import shutil
from datetime import datetime

# Import generation functions
from generate_i2v import load_pipeline, generate_video

# Initialize FastAPI
app = FastAPI(
    title="LTX Video I2V API",
    description="Image-to-Video generation using LTX Video 13B",
    version="1.0.0"
)

# CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline and job storage
pipe = None
jobs = {}
UPLOAD_DIR = "/workspace/uploads"
OUTPUT_DIR = "/workspace/outputs"


class GenerateRequest(BaseModel):
    """Request model for video generation"""
    image_url: str  # Can be URL or path
    prompt: str
    seed: Optional[int] = 42
    width: Optional[int] = 1280
    height: Optional[int] = 720
    num_frames: Optional[int] = 121


class JobStatus(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str  # 'queued', 'processing', 'done', 'error'
    created_at: str
    completed_at: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None
    generation_time: Optional[float] = None


@app.on_event("startup")
async def startup():
    """Load model on server startup"""
    global pipe
    print("Loading LTX Video pipeline...")
    pipe = load_pipeline()
    
    # Create directories
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Server ready!")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "model": "LTX Video 13B Distilled",
        "resolution": "720p",
        "active_jobs": len([j for j in jobs.values() if j['status'] == 'processing'])
    }


@app.post("/generate")
async def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Start async video generation
    
    Returns job_id for status polling
    """
    job_id = str(uuid.uuid4())[:8]
    
    jobs[job_id] = {
        'status': 'queued',
        'created_at': datetime.now().isoformat(),
        'request': req.dict()
    }
    
    # Process in background
    background_tasks.add_task(process_job, job_id, req)
    
    return {"job_id": job_id, "status": "queued"}


@app.post("/generate/sync")
async def generate_sync(req: GenerateRequest):
    """
    Synchronous video generation (blocks until complete)
    
    Use for single requests when you can wait
    """
    job_id = str(uuid.uuid4())[:8]
    
    try:
        start = time.time()
        path = generate_video(
            pipe,
            req.image_url,
            req.prompt,
            job_id,
            req.seed
        )
        elapsed = time.time() - start
        
        return {
            "job_id": job_id,
            "status": "done",
            "path": path,
            "generation_time": round(elapsed, 1),
            "download_url": f"/download/{job_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def process_job(job_id: str, req: GenerateRequest):
    """Background task for video generation"""
    jobs[job_id]['status'] = 'processing'
    
    try:
        start = time.time()
        path = generate_video(
            pipe,
            req.image_url,
            req.prompt,
            job_id,
            req.seed
        )
        elapsed = time.time() - start
        
        jobs[job_id].update({
            'status': 'done',
            'path': path,
            'completed_at': datetime.now().isoformat(),
            'generation_time': round(elapsed, 1)
        })
    except Exception as e:
        jobs[job_id].update({
            'status': 'error',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        })


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Check job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job['status'],
        "created_at": job['created_at'],
        "completed_at": job.get('completed_at'),
        "generation_time": job.get('generation_time'),
        "error": job.get('error'),
        "download_url": f"/download/{job_id}" if job['status'] == 'done' else None
    }


@app.get("/download/{job_id}")
async def download(job_id: str):
    """Download generated video"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job['status'] != 'done':
        raise HTTPException(status_code=400, detail=f"Video not ready. Status: {job['status']}")
    
    path = job['path']
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"{job_id}.mp4"
    )


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image for processing
    
    Returns the path to use in generate request
    """
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4()[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    return {
        "filename": filename,
        "path": filepath,
        "message": "Use this path in your generate request"
    }


@app.get("/jobs")
async def list_jobs(limit: int = 20):
    """List recent jobs"""
    sorted_jobs = sorted(
        jobs.items(),
        key=lambda x: x[1]['created_at'],
        reverse=True
    )[:limit]
    
    return [
        {
            "job_id": job_id,
            "status": job['status'],
            "created_at": job['created_at']
        }
        for job_id, job in sorted_jobs
    ]


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its video file"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Delete video file if exists
    if job.get('path') and os.path.exists(job['path']):
        os.remove(job['path'])
    
    del jobs[job_id]
    return {"message": f"Job {job_id} deleted"}


# Run with: uvicorn api_server:app --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
