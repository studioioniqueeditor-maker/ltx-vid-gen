import runpod
import sys
import os
import traceback

# ----------------------------------------------------------------------------
# DEBUG: Early Logging to catch import crashes
# ----------------------------------------------------------------------------
print("--- HANDLER STARTUP ---")
print(f"Python Version: {sys.version}")
try:
    import torch
    print(f"Torch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
except ImportError as e:
    print(f"CRITICAL: Failed to import torch: {e}")
except Exception as e:
    print(f"CRITICAL: Error checking CUDA: {e}")

# ----------------------------------------------------------------------------
# IMPORTS
# ----------------------------------------------------------------------------
try:
    import base64
    from generate_i2v import LTXVideoGenerator
except Exception as e:
    print("CRITICAL: Failed to import application modules")
    traceback.print_exc()
    sys.exit(1)

# GLOBAL VARIABLE
generator = None

def init_model():
    global generator
    if generator is None:
        try:
            print("--- Loading Model into VRAM ---")
            
            # Check common mount paths
            possible_paths = [
                "/workspace/ltx-models",  # Manual mount path
                "/runpod-volume/ltx-models", # Default RunPod Serverless mount if folder exists
                "/runpod-volume" # If files are in root of volume
            ]
            
            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    # Check if it actually contains the model file we need
                    if os.path.exists(os.path.join(path, "model_index.json")) or \
                       os.path.exists(os.path.join(path, "ltxv-13b-0.9.8-distilled-fp8.safetensors")):
                        model_path = path
                        print(f"Found model at: {model_path}")
                        break
            
            if model_path is None:
                # DEBUG: List directories to find where it is
                print("DEBUG: Could not find model. Listing root directories:")
                for root_dir in ["/workspace", "/runpod-volume"]:
                    if os.path.exists(root_dir):
                        print(f"Listing {root_dir}:")
                        for f in os.listdir(root_dir):
                            print(f" - {f}")
                    else:
                        print(f"{root_dir} does not exist.")
                
                # Fallback to original default to let it fail with specific error
                model_path = "/workspace/ltx-models"

            generator = LTXVideoGenerator(model_path=model_path)
        except Exception as e:
            print(f"CRITICAL: Model initialization failed: {e}")
            traceback.print_exc()
            raise e
    return generator

def encode_video_to_base64(video_path):
    with open(video_path, "rb") as video_file:
        encoded_string = base64.b64encode(video_file.read()).decode('utf-8')
    return encoded_string

def handler(job):
    print(f"Received job: {job.get('id')}")
    
    try:
        # Initialize model inside handler to capture errors in job logs if possible
        gen = init_model()
        
        job_input = job["input"]
        prompt = job_input.get("prompt")
        image_url = job_input.get("image_url")
        
            # Optional parameters
            width = job_input.get("width", 1280)
            height = job_input.get("height", 720)
            
            # Validation: Ensure divisible by 32 (LTX requirement)
            if width % 32 != 0:
                new_width = (width // 32) * 32
                print(f"WARNING: Width {width} not divisible by 32. Snapping to {new_width}")
                width = new_width
                
            if height % 32 != 0:
                new_height = (height // 32) * 32
                print(f"WARNING: Height {height} not divisible by 32. Snapping to {new_height}")
                height = new_height
            
            num_frames = job_input.get("num_frames", 121)        num_steps = job_input.get("num_steps", 8)
        seed = job_input.get("seed", 42)
        
        if not prompt or not image_url:
            return {"error": "Prompt and image_url are required."}
        
        # Run inference
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
        print(f"ERROR processing job: {e}")
        traceback.print_exc()
        return {"error": f"An error occurred: {str(e)}"}

print("--- Starting RunPod Serverless Listener ---")
runpod.serverless.start({"handler": handler})
