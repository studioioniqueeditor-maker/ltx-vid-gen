import os
import sys
import traceback

# Force stdout flushing
sys.stdout.reconfigure(line_buffering=True)

print("DEBUG: importing ltx_video...")
try:
    # The LTX-Video repo will be cloned to /workspace/LTX-Video in the container.
    # Locally, we expect it to be in the path provided or in PYTHONPATH.
    from ltx_video.inference import infer, InferenceConfig
    print("DEBUG: ltx_video imported successfully.")
except ImportError as e:
    print(f"WARNING: ltx_video module not found or failed to import: {e}")
    traceback.print_exc()
    # Placeholders for unit tests or failure mode
    def infer(*args, **kwargs): raise ImportError("ltx_video not available")
    class InferenceConfig:
        def __init__(self, *args, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
except Exception as e:
    print(f"CRITICAL ERROR during ltx_video import: {e}")
    traceback.print_exc()
    raise e

class LTXInferenceEngine:
    def __init__(self, repo_path="/workspace/LTX-Video", config_file="configs/ltxv-2b-0.9.8-distilled-fp8.yaml"):
        self.repo_path = repo_path
        self.config_file = config_file
        
    def generate_video(
        self, 
        prompt, 
        image_path, 
        output_path="output.mp4",
        width=1216,
        height=704,
        num_frames=121,
        seed=42,
        guidance_scale=3.0,
        num_steps=30
    ):
        print(f"Generating video for prompt: {prompt}")
        
        # Ensure config path is absolute if it's relative to repo
        pipeline_config = self.config_file
        if not os.path.isabs(pipeline_config):
            pipeline_config = os.path.join(self.repo_path, pipeline_config)

        config = InferenceConfig(
            pipeline_config=pipeline_config,
            prompt=prompt,
            conditioning_media_paths=[image_path],
            conditioning_start_frames=[0],
            height=height,
            width=width,
            num_frames=num_frames,
            output_path=output_path,
            seed=seed,
            # Note: InferenceConfig might have different attribute names depending on the repo version.
            # We follow the guide's parameters.
        )
        
        # Inject additional params if InferenceConfig supports them directly 
        # or if they are passed to infer. 
        # Based on Method 2 in the guide:
        try:
            infer(config)
            print(f"Video generated successfully: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error during inference: {e}")
            raise e
