import os
import sys
import base64
import time
import requests
from dotenv import load_dotenv

# Load client environment variables
load_dotenv(".env.client")

# Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")

if not all([RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID]):
    print("Error: Missing required environment variables in .env.client")
    print("Ensure RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID are set.")
    sys.exit(1)

RUNPOD_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"

def encode_image_to_base64(image_path):
    """Encodes a local image to base64."""
    print(f"Encoding image: {image_path}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def run_inference(image_base64, prompt):
    print(f"Sending request to RunPod Endpoint: {RUNPOD_ENDPOINT_ID} (using image_base64)...")
    
    payload = {
        "input": {
            "prompt": prompt,
            "image_base64": image_base64,
            "num_frames": 121,
            "num_steps": 30,
            "seed": 42
        }
    }
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Using a long timeout for video generation
    try:
        response = requests.post(RUNPOD_URL, json=payload, headers=headers, timeout=600)
    except Exception as e:
        print(f"Request failed: {e}")
        return None
    
    if response.status_code != 200:
        print(f"Error: RunPod API returned status {response.status_code}")
        print(response.text)
        return None
        
    data = response.json()
    
    if "error" in data:
        print(f"Error from RunPod: {data['error']}")
        return None
        
    if "output" in data:
        return data["output"]
    
    return data

def save_video(base64_string, output_path):
    print(f"Decoding video to {output_path}...")
    video_data = base64.b64decode(base64_string)
    with open(output_path, "wb") as f:
        f.write(video_data)
    print("Video saved successfully!")

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_serverless_base64.py <image_path> <prompt>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    prompt = sys.argv[2]
    
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        sys.exit(1)
        
    # 1. Encode Image
    image_base64 = encode_image_to_base64(image_path)
    
    # 2. Run Inference
    start_time = time.time()
    result = run_inference(image_base64, prompt)
    duration = time.time() - start_time
    
    if result and "video_base64" in result:
        # 3. Save Video
        timestamp = int(time.time())
        output_filename = f"serverless_base64_output_{timestamp}.mp4"
        save_video(result["video_base64"], output_filename)
        print(f"Total time elapsed: {duration:.2f} seconds")
    else:
        print("Failed to get video_base64 from response.")
        if result:
            print(f"Full response: {result}")

if __name__ == "__main__":
    main()
