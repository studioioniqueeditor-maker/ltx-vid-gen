import os
import sys
import time
import requests
import base64
from uploader import GCSUploader

# Try to load dotenv
try:
    from dotenv import load_dotenv
    load_dotenv(".env.client") # Load specific client env file
except ImportError:
    print("Warning: python-dotenv not installed. Relying on system env vars.")

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_SERVICE_ACCOUNT_JSON = os.getenv("GCS_SERVICE_ACCOUNT_JSON") # Optional if using ADC

# Job Config
INPUT_IMAGE_PATH = r'/Users/aditya/Documents/Liston Images/scene 36.png' # RENAME THIS to your local file
PROMPT = "A cinematic slow dolly zoom in, 30fps smooth motion"
OUTPUT_FILENAME = "output/scene-36-dolly-in.mp4"

def main():
    print("--- LTX Video Gen: End-to-End Test Workflow (GCP) ---")
    
    # 1. Checks
    if not os.path.exists(INPUT_IMAGE_PATH):
        print(f"Error: Input file '{INPUT_IMAGE_PATH}' not found.")
        print("Please edit 'INPUT_IMAGE_PATH' in this script or create the file.")
        return

    if not all([RUNPOD_ENDPOINT_ID, RUNPOD_API_KEY, GCS_BUCKET_NAME]):
        print("Error: Missing environment variables.")
        print("Please check .env.client file (RUNPOD_*, GCS_BUCKET_NAME).")
        return

    # 2. Upload Image
    print("\n[Step 1] Uploading Image to Google Cloud Storage...")
    uploader = GCSUploader(GCS_BUCKET_NAME, GCS_SERVICE_ACCOUNT_JSON)
    try:
        image_url = uploader.upload_file(INPUT_IMAGE_PATH)
        print(f"Image URL: {image_url}")
    except Exception as e:
        print(f"Upload failed: {e}")
        return

    # 3. Submit Job (Async)
    print(f"\n[Step 2] Sending Job to RunPod (Async)...")
    # Change runsync to run
    api_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run"
    
    payload = {
        "input": {
            "prompt": PROMPT,
            "image_url": image_url,
            "width": 1280,
            "height": 720,
            "num_frames": 121, 
            "num_steps": 30
        }
    }
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Start Job
        start_time = time.time()
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        
        if response.status_code != 200:
            print(f"Error starting job: {response.text}")
            return

        job_data = response.json()
        job_id = job_data.get("id")
        print(f"Job initiated. ID: {job_id}")
        
        # 4. Poll for Completion
        print(f"\n[Step 3] Polling for results (this may take minutes)...")
        status_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}"
        
        while True:
            status_res = requests.get(status_url, headers=headers, timeout=30)
            if status_res.status_code != 200:
                print(f"Error polling status: {status_res.text}")
                time.sleep(5)
                continue
                
            status_data = status_res.json()
            status = status_data.get("status")
            
            if status == "COMPLETED":
                print("\nJob COMPLETED!")
                output = status_data.get("output", {})
                break
            elif status == "FAILED":
                print(f"\nJob FAILED.")
                print(f"Error: {status_data.get('error')}")
                return
            elif status in ["IN_QUEUE", "IN_PROGRESS"]:
                sys.stdout.write(f"\rStatus: {status} ({int(time.time() - start_time)}s elapsed)...")
                sys.stdout.flush()
                time.sleep(5)
            else:
                print(f"\nUnknown status: {status}")
                time.sleep(5)

        # 5. Extract and Save Video
        video_b64 = None
        if isinstance(output, dict):
            video_b64 = output.get("video_base64")
        
        # Sometimes RunPod returns the output directly if not dict wrapped, check handling
        if not video_b64 and "video_base64" in str(output):
             # Fallback parsing if needed, but standard should be dict
             pass

        if not video_b64:
            print("\nNo video_base64 found in output.")
            print(f"Output keys: {output.keys() if isinstance(output, dict) else output}")
            return

        print(f"\n[Step 4] Saving Video ({len(video_b64)} bytes)...")
        video_bytes = base64.b64decode(video_b64)
        with open(OUTPUT_FILENAME, "wb") as f:
            f.write(video_bytes)
            
        elapsed = time.time() - start_time
        print(f"SUCCESS! Video saved to {os.path.abspath(OUTPUT_FILENAME)}")
        print(f"Total time: {elapsed:.2f}s")

    except Exception as e:
        print(f"\nAPI Request Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
