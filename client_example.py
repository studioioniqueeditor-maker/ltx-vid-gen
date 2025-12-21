import requests
import base64
import os
import sys

# Configuration
API_ENDPOINT = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"
API_KEY = "YOUR_RUNPOD_API_KEY"

# Input Configuration
IMAGE_URL = "https://example.com/path/to/your/image.jpg" # MUST be a publicly accessible URL
PROMPT = "A cinematic shot of a futuristic city"

OUTPUT_FILE = "output_video.mp4"

def test_remote_api():
    print(f"--- Testing Remote API: {API_ENDPOINT} ---")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "prompt": PROMPT,
            "image_url": IMAGE_URL,
            "width": 1280,
            "height": 720,
            "num_frames": 121,
            "num_steps": 30
        }
    }
    
    print("Sending request...")
    try:
        response = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=600)
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return

        data = response.json()
        
        # Check for RunPod specific status (if using run/status pattern, this script assumes runsync)
        if "error" in data:
            print(f"API Error: {data['error']}")
            return

        # Handle 'output' field from RunPod standard response
        output = data.get("output", {})
        
        # Check if output contains the video_base64 directly or inside another dict
        # Based on handler.py: return {"video_base64": ...}
        # RunPod wraps handler output in "output" key.
        
        video_b64 = output.get("video_base64")
        
        if not video_b64:
            print("Error: No video_base64 found in response.")
            print(f"Response keys: {data.keys()}")
            if "output" in data:
                print(f"Output keys: {data['output'].keys()}")
            return

        print(f"Success! Received {len(video_b64)} bytes of base64 data.")
        
        # Decode and save
        video_bytes = base64.b64decode(video_b64)
        with open(OUTPUT_FILE, "wb") as f:
            f.write(video_bytes)
            
        print(f"Video saved to {os.path.abspath(OUTPUT_FILE)}")
        
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("This script is a template. Please edit API_ENDPOINT and IMAGE_URL before running.")
    # test_remote_api() # Uncomment to run
