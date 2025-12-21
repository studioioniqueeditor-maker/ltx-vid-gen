import os
import sys
import base64
import time
import requests
from dotenv import load_dotenv
from google.cloud import storage

# Load client environment variables
load_dotenv(".env.client")

# Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH", "oci_private_key.pem") # Assuming this is the key file

if not all([RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID, GCP_BUCKET_NAME]):
    print("Error: Missing required environment variables in .env.client")
    print("Ensure RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID, and GCP_BUCKET_NAME are set.")
    sys.exit(1)

RUNPOD_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"

def upload_to_gcp(local_file_path, destination_blob_name):
    """Uploads a file to the bucket."""
    print(f"Uploading {local_file_path} to gs://{GCP_BUCKET_NAME}/{destination_blob_name}...")
    
    # Initialize client (assumes GOOGLE_APPLICATION_CREDENTIALS is set or using default auth)
    # If GCP_CREDENTIALS_PATH is set, explicitly use it
    if os.path.exists(GCP_CREDENTIALS_PATH):
        client = storage.Client.from_service_account_json(GCP_CREDENTIALS_PATH)
    else:
        # Fallback to default environment auth
        client = storage.Client()
        
    bucket = client.bucket(GCP_BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(local_file_path)
    
    # Make public (optional, but often needed for simple URL access if not using signed URLs)
    # Ideally, we should generate a signed URL, but for testing public read is easier if bucket allows.
    # If bucket is private, we must use a signed URL.
    
    # Let's try generating a signed URL valid for 15 minutes
    url = blob.generate_signed_url(
        version="v4",
        expiration=900, # 15 minutes
        method="GET"
    )
    
    print(f"File uploaded. Signed URL: {url}")
    return url

def run_inference(image_url, prompt):
    print(f"Sending request to RunPod Endpoint: {RUNPOD_ENDPOINT_ID}...")
    
    payload = {
        "input": {
            "prompt": prompt,
            "image_url": image_url,
            "num_frames": 121,
            "num_steps": 30,
            "seed": 42
        }
    }
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(RUNPOD_URL, json=payload, headers=headers, timeout=300)
    
    if response.status_code != 200:
        print(f"Error: RunPod API returned status {response.status_code}")
        print(response.text)
        return None
        
    data = response.json()
    
    if "error" in data:
        print(f"Error from RunPod: {data['error']}")
        return None
        
    # Handle both sync and async responses if runsync wasn't used properly or timed out
    # For runsync, the output is usually in 'output'
    if "output" in data:
        return data["output"]
    
    # If it returned a job ID (async), we might need to poll, but we used runsync.
    # Sometimes runsync returns status: "IN_QUEUE" if it times out.
    print(f"Unexpected response structure: {data.keys()}")
    return data

def save_video(base64_string, output_path):
    print(f"Decoding video to {output_path}...")
    video_data = base64.b64decode(base64_string)
    with open(output_path, "wb") as f:
        f.write(video_data)
    print("Video saved successfully!")

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_serverless.py <image_path> <prompt>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    prompt = sys.argv[2]
    
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        sys.exit(1)
        
    # 1. Upload Image
    timestamp = int(time.time())
    blob_name = f"test_inputs/input_{timestamp}.jpg"
    try:
        image_url = upload_to_gcp(image_path, blob_name)
    except Exception as e:
        print(f"Failed to upload to GCP: {e}")
        sys.exit(1)
        
    # 2. Run Inference
    result = run_inference(image_url, prompt)
    
    if result and "video_base64" in result:
        # 3. Save Video
        output_filename = f"serverless_output_{timestamp}.mp4"
        save_video(result["video_base64"], output_filename)
    else:
        print("Failed to get video_base64 from response.")
        if result:
            print(f"Full response: {result}")

if __name__ == "__main__":
    main()
