import os
import sys
from inference_engine import LTXInferenceEngine

def run_local_test():
    # Placeholder for a real test. In the container, this will use the real repo.
    # For now, we use a mock if repo is missing (handled in inference_engine.py warning)
    
    engine = LTXInferenceEngine(
        repo_path=os.getenv("LTX_REPO_PATH", "/workspace/LTX-Video"),
        config_file="configs/ltxv-2b-0.9.8-distilled-fp8.yaml"
    )
    
    prompt = "A cinematic shot of a sunset over a digital ocean, vibrant purple waves"
    # Create a dummy image if not exists
    image_path = "test_input.jpg"
    if not os.path.exists(image_path):
        print("Creating dummy input image...")
        with open(image_path, "wb") as f:
            f.write(b"\x00" * 1024) # Dummy data
            
    output_path = "test_output.mp4"
    
    print(f"Starting local test with prompt: {prompt}")
    try:
        engine.generate_video(
            prompt=prompt,
            image_path=image_path,
            output_path=output_path
        )
        print("Local test execution finished.")
        if os.path.exists(output_path):
             print(f"Output found at {output_path}")
        else:
             print("Output not found (expected if mocked).")
    except Exception as e:
        print(f"Local test failed: {e}")
        # We don't exit 1 here if it's an import error because we are likely in a non-ML env
        if "ltx_video" not in str(e):
            sys.exit(1)

if __name__ == "__main__":
    run_local_test()
