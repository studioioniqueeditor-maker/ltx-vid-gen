import os
import sys
from huggingface_hub import snapshot_download

def download_distilled_model(target_dir="/workspace/ltx-models"):
    print(f"Starting download of LTX-Video 2B Distilled FP8 weights to {target_dir}...")
    try:
        os.makedirs(target_dir, exist_ok=True)
        
        repo_id = "Lightricks/LTX-Video"
        
        # We only want the 2B distilled FP8 files and necessary configs
        allow_patterns = [
            "**/*2b*distilled*fp8*",  # Matches ltxv-2b... in root or configs/ or checkpoints/
            "**/*.json",              # Configs like config.json, scheduler_config.json anywhere
            "**/*.txt",               # License, requirements
            "*.md",                # README in root
            "scheduler/**",         # Scheduler configs
            "tokenizer/**",         # Tokenizer files
            "text_encoder/**",      # Text encoder files
            "transformer/**",       # Transformer config
            "vae/**",                # VAE config
            "configs/**"            # Ensure all configs are downloaded just in case
        ]
        
        # Exclude 13B models to save space/time
        ignore_patterns = [
            "*13b*",
            "*pixart*",
            "*.bin" # Often redundant if safetensors exist, but be careful.
        ]
        
        snapshot_download(
            repo_id=repo_id,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns
        )
        print(f"Download complete: {target_dir}")
        return True
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False

if __name__ == "__main__":
    target = os.getenv("MODEL_PATH", "./models")
    success = download_distilled_model(target_dir=target)
    if not success:
        sys.exit(1)
    sys.exit(0)
