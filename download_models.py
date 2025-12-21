import os
import sys
from huggingface_hub import snapshot_download

def download_ltx_model(model_id="Lightricks/LTX-Video", target_dir="/workspace/ltx-models"):
    print(f"Starting download of {model_id} to {target_dir}...")
    try:
        os.makedirs(target_dir, exist_ok=True)
        # We download the repository. For the 2B distilled version, we might need specific files or just the whole repo.
        # Based on common patterns, the distilled weights are part of the main repo or a separate one.
        # If it's a separate repo like 'Lightricks/LTX-Video-2B-v0.9.1', we use that.
        # Given the guide mentions 'ltx-video-2b-v0.9.1', let's try to be precise if possible, 
        # but snapshot_download on the main repo is safer if the user hasn't specified the exact HF repo ID.
        
        # However, the user said "follow the documentation provided in ltx-guide-nblm.md".
        # The guide doesn't specify the HF repo ID, only the config path.
        
        repo_id = "Lightricks/LTX-Video" # Defaulting to the main repo which contains versions
        
        snapshot_download(
            repo_id=repo_id,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            # We can filter for 2B distilled if we know the pattern, but let's get the whole thing for robustness
            # since we have 80GB VRAM and likely enough disk space on network volume.
        )
        print(f"Download complete: {target_dir}")
        return True
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False

if __name__ == "__main__":
    # In local testing, we might want to download to a local 'models' folder
    target = os.getenv("MODEL_PATH", "./models")
    success = download_ltx_model(target_dir=target)
    if not success:
        sys.exit(1)
    sys.exit(0)
