import runpod
import os
import base64
import requests
import uuid
import shutil
import sys
import traceback

from inference_engine import LTXInferenceEngine

# Initialize the inference engine
# Defaults for RunPod environment
REPO_PATH = os.getenv("LTX_REPO_PATH", "/workspace/LTX-Video")
CONFIG_FILE = os.getenv("LTX_CONFIG_FILE", "configs/ltxv-2b-0.9.8-distilled-fp8.yaml")
MODEL_PATH = os.getenv("MODEL_PATH", "/workspace/ltx-models")

print("--- WORKER STARTUP ---")
print(f"REPO_PATH: {REPO_PATH}")
print(f"CONFIG_FILE: {CONFIG_FILE}")
print(f"MODEL_PATH: {MODEL_PATH}")

# Verify model path existence
if not os.path.exists(MODEL_PATH):
    print(f"WARNING: MODEL_PATH {MODEL_PATH} does not exist. Worker might fail inference.")
else:
    print(f"INFO: MODEL_PATH {MODEL_PATH} exists.")

try:
    engine = LTXInferenceEngine(repo_path=REPO_PATH, config_file=CONFIG_FILE)
    print("SUCCESS: Inference Engine initialized.")
except Exception as e:
    print(f"CRITICAL ERROR initializing engine: {e}")
    traceback.print_exc()
    # We allow the handler to start so we can report the error in the first request if needed, 
    # but usually this means the worker is dead.
    engine = None

def download_image(url):
    print(f"Downloading image from: {url}")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        file_path = f"/tmp/{uuid.uuid4()}.jpg"
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        return file_path
    else:
        raise Exception(f"Failed to download image from {url}, status code: {response.status_code}")

def encode_video_to_base64(video_path):
    print(f"Encoding video to base64: {video_path}")
    with open(video_path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode('utf-8')

def handler(job):
    job_input = job.get("input", {})
    
    # 1. Validation
    prompt = job_input.get("prompt")
    image_url = job_input.get("image_url")
    image_base64 = job_input.get("image_base64")
    
    if not prompt:
        return {"error": "Missing 'prompt' in input"}
    if not image_url and not image_base64:
        return {"error": "Missing 'image_url' or 'image_base64' in input"}
        
    temp_files = []
    
    try:
        # 2. Prepare Input Image
        if image_url:
            input_image_path = download_image(image_url)
        else:
            # Decode base64 image
            input_image_path = f"/tmp/{uuid.uuid4()}.jpg"
            with open(input_image_path, "wb") as f:
                f.write(base64.b64decode(image_base64))
        
        temp_files.append(input_image_path)
        
        # 3. Generate Video
        output_path = f"/tmp/{uuid.uuid4()}.mp4"
        engine.generate_video(
            prompt=prompt,
            image_path=input_image_path,
            output_path=output_path,
            width=job_input.get("width", 1216),
            height=job_input.get("height", 704),
            num_frames=job_input.get("num_frames", 121),
            seed=job_input.get("seed", 42),
            num_steps=job_input.get("num_steps", 30)
        )
        
        temp_files.append(output_path)
        
        # 4. Return result
        video_base64 = encode_video_to_base64(output_path)
        
        return {"video_base64": video_base64}
        
    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e)}
    finally:
        # Cleanup
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    print("Starting RunPod Serverless Handler...")
    runpod.serverless.start({"handler": handler})
