"""
LTX Video 13B Image-to-Video Generator
Optimized for RunPod A100/H100
"""

import torch
import os
import time
from diffusers import LTXVideoTransformer3DModel, LTXPipeline
from diffusers.utils import export_to_video, load_image
from huggingface_hub import hf_hub_download

# Configuration
# This path should point to the volume mount: /workspace/ltx-models
DEFAULT_MODEL_PATH = '/workspace/ltx-models'

class LTXVideoGenerator:
    def __init__(self, model_path=DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self.pipe = self._load_pipeline()

    def _load_pipeline(self):
        print(f"Loading LTX Video model from {self.model_path}...")
        
        # Check for FP8 single file specifically
        fp8_file = os.path.join(self.model_path, "ltxv-13b-0.9.8-distilled-fp8.safetensors")
        
        if os.path.exists(fp8_file):
            print(f"Found FP8 checkpoint: {fp8_file}")
            # Load the transformer from the single file
            transformer = LTXVideoTransformer3DModel.from_single_file(
                fp8_file, 
                torch_dtype=torch.float8_e4m3fn
            )
            # Load the rest of the pipeline from the folder structure
            pipe = LTXPipeline.from_pretrained(
                self.model_path,
                transformer=transformer,
                torch_dtype=torch.bfloat16
            )
        else:
            print("Loading standard model (folder structure)...")
            pipe = LTXPipeline.from_pretrained(
                self.model_path,
                torch_dtype=torch.bfloat16
            )

        pipe.to("cuda")
        # pipe.vae.enable_tiling() # Optional: Enable if VRAM is tight, but usually fine on A100
        
        print("Model loaded successfully!")
        return pipe

    def generate(self, prompt, image_path, width=1280, height=720, num_frames=121, num_steps=8, seed=42):
        """
        Generate video from image
        """
        try:
            image = load_image(image_path)
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")

        negative_prompt = "worst quality, inconsistent motion, blurry, jittery, distorted"
        
        print(f"Generating video...")
        print(f"  Prompt: {prompt}")

        try:
            video = self.pipe(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                num_inference_steps=num_steps,
                generator=torch.Generator().manual_seed(seed),
                output_type="pil"
            ).frames[0]
        except Exception as e:
            raise Exception(f"Video generation failed: {e}")

        # Save output temporarily
        output_dir = "/tmp/outputs"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = int(time.time())
        output_filename = f"generated_{timestamp}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        export_to_video(video, output_path, fps=24)
        print(f"Saved local video: {output_path}")
        
        return output_path