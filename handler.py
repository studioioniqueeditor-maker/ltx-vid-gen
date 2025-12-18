import runpod
import torch
from generate_i2v import LTXVideoGenerator
from storage import upload_to_storage

# GLOBAL VARIABLE: This stays in memory between serverless calls
generator = None

def init_model():
    global generator
    if generator is None:
        print("--- Loading Model into VRAM ---")
        # Point this to your mounted Network Volume path!
        model_path = "/workspace/ltx-models"
        generator = LTXVideoGenerator(model_path=model_path)
    return generator

def handler(job):
    # This ensures the model is loaded once per worker lifecycle
    gen = init_model()
    
    job_input = job["input"]
    prompt = job_input.get("prompt")
    image_url = job_input.get("image_url")
    
    # Basic input validation (could be moved to validation.py later if needed)
    if not prompt or not image_url:
        return {"error": "Prompt and image_url are required."}
    
    # Run inference
    try:
        video_path = gen.generate(prompt, image_url)
        # Use your storage.py to upload to S3/GCS
        url = upload_to_storage(video_path)
    except Exception as e:
        return {"error": f"An error occurred during video generation: {str(e)}"}
    
    return {"video_url": url}

runpod.serverless.start({"handler": handler})