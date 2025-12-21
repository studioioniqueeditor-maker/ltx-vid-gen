import os
import sys
import mimetypes

try:
    from google.cloud import storage
    from google.api_core.exceptions import Forbidden
except ImportError:
    print("Error: 'google-cloud-storage' library is required for GCS uploads.")
    print("Please install it: pip install google-cloud-storage")
    sys.exit(1)

class GCSUploader:
    def __init__(self, bucket_name, service_account_json=None):
        """
        Initialize GCS Uploader.
        
        Args:
            bucket_name (str): Name of the GCS bucket
            service_account_json (str, optional): Path to service account JSON file. 
                                                  If None, looks for GOOGLE_APPLICATION_CREDENTIALS env var 
                                                  or uses default gcloud auth.
        """
        self.bucket_name = bucket_name
        
        try:
            if service_account_json and os.path.exists(service_account_json):
                print(f"Using service account file: {service_account_json}")
                self.client = storage.Client.from_service_account_json(service_account_json)
            else:
                # Use Application Default Credentials (ADC)
                self.client = storage.Client()
                
            self.bucket = self.client.bucket(bucket_name)
        except Exception as e:
            print(f"Failed to initialize GCS Client: {e}")
            sys.exit(1)

    def upload_file(self, file_path):
        """
        Uploads a file to GCS and makes it public.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        blob = self.bucket.blob(file_name)
        
        # Detect Content-Type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        print(f"Uploading {file_name} to gs://{self.bucket_name}...")
        
        try:
            # Upload
            blob.upload_from_filename(file_path, content_type=content_type)
            
            # Make Public
            # Note: This requires the bucket/user to have permission to set ACLs.
            # Alternative: Generate a signed URL if you don't want to make it public.
            try:
                blob.make_public()
                print("File made public.")
                return blob.public_url
            except Forbidden:
                print("Warning: Could not make file public (ACL permission denied).")
                print("Attempting to generate a Signed URL instead (valid for 1 hour)...")
                # Fallback to Signed URL
                url = blob.generate_signed_url(
                    version="v4",
                    expiration=3600, # 1 hour
                    method="GET"
                )
                return url

        except Exception as e:
            print(f"Failed to upload: {e}")
            raise e

if __name__ == "__main__":
    # Test
    bucket = os.getenv("GCS_BUCKET_NAME")
    json_path = os.getenv("GCS_SERVICE_ACCOUNT_JSON")
    
    if not bucket:
        print("Set GCS_BUCKET_NAME to test.")
    else:
        uploader = GCSUploader(bucket, json_path)
        with open("test_gcp.txt", "w") as f: f.write("test gcp")
        try:
            url = uploader.upload_file("test_gcp.txt")
            print(f"URL: {url}")
        finally:
            if os.path.exists("test_gcp.txt"): os.remove("test_gcp.txt")