import runpod
import torch
import base64
import os
from generate_i2v import LTXVideoGenerator

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

def encode_video_to_base64(video_path):
    with open(video_path, "rb") as video_file:
        encoded_string = base64.b64encode(video_file.read()).decode('utf-8')
    return encoded_string

def handler(job):
    # This ensures the model is loaded once per worker lifecycle
    gen = init_model()
    
    job_input = job["input"]
    prompt = job_input.get("prompt")
    image_url = job_input.get("image_url")
    
    # Optional parameters
    width = job_input.get("width", 1280)
    height = job_input.get("height", 720)
    num_frames = job_input.get("num_frames", 121)
    num_steps = job_input.get("num_steps", 8)
    seed = job_input.get("seed", 42)
    
    if not prompt or not image_url:
        return {"error": "Prompt and image_url are required."}
    
    # Run inference
    try:
        video_path = gen.generate(
            prompt=prompt, 
            image_path=image_url,
            width=width,
            height=height,
            num_frames=num_frames,
            num_steps=num_steps,
            seed=seed
        )
        
        # Encode to Base64
        video_base64 = encode_video_to_base64(video_path)
        
        # Cleanup local file
        if os.path.exists(video_path):
            os.remove(video_path)
            
        return {"video_base64": video_base64}
        
    except Exception as e:
        return {"error": f"An error occurred during video generation: {str(e)}"}

runpod.serverless.start({"handler": handler})