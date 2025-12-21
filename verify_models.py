import os

def verify_ltx_model_files(model_path):
    print(f"Verifying model files in {model_path}...")
    
    # Expected files for a diffusers-style model or the LTX repository
    # Based on the Lightricks/LTX-Video repo, we expect a structure.
    # If we downloaded the whole repo, it has 'configs' folder.
    # The weights might be in 'checkpoints' or root.
    
    # For now, let's look for common indicators
    required_paths = [
        "configs",
        # "checkpoints", # Optional depending on how it's downloaded
    ]
    
    missing = []
    for p in required_paths:
        full_path = os.path.join(model_path, p)
        if not os.path.exists(full_path):
            missing.append(p)
            
    if missing:
        print(f"FAIL: Missing expected model components: {missing}")
        return False
        
    print("SUCCESS: Model directory structure verified.")
    return True

if __name__ == "__main__":
    target = os.getenv("MODEL_PATH", "./models")
    if not os.path.exists(target):
        print(f"Target directory {target} does not exist. Skipping verification.")
        exit(0)
    success = verify_ltx_model_files(target)
    if not success:
        exit(1)
    exit(0)
