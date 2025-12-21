"""
LTX Video 13B Image-to-Video Generator
Optimized for RunPod A100/H100
"""

import torch
import os
import time
from huggingface_hub import hf_hub_download

try:
    from diffusers import LTXImageToVideoPipeline, LTXVideoTransformer3DModel
    from diffusers.utils import export_to_video, load_image
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import diffusers modules: {e}")
    # Fallback/Debug info
    import diffusers
    print(f"Diffusers version: {diffusers.__version__}")
    print(f"Available modules in diffusers: {dir(diffusers)}")
    raise e

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
            # FORCE CAST TO BFLOAT16 to avoid matmul errors
            # The weights are loaded as FP8, but we run computation in BF16
            transformer = transformer.to(dtype=torch.bfloat16)
            
            # Load the rest of the pipeline from the folder structure
            # Use LTXImageToVideoPipeline explicitly
            pipe = LTXImageToVideoPipeline.from_pretrained(
                self.model_path,
                transformer=transformer,
                torch_dtype=torch.bfloat16
            )
        else:
            print("Loading standard model (folder structure)...")
            pipe = LTXImageToVideoPipeline.from_pretrained(
                self.model_path,
                torch_dtype=torch.bfloat16
            )

        pipe.to("cuda")
        
        # CRITICAL: VAE must be Float32 to avoid generation artifacts/noise
        print("Ensuring VAE is in Float32...")
        pipe.vae = pipe.vae.to(dtype=torch.float32)
        
        # MEMORY OPTIMIZATIONS
        print("Enabling memory optimizations (VAE Tiling & Slicing)...")
        pipe.vae.enable_tiling()
        pipe.vae.enable_slicing()
        
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
            # 1. Generate Latents (BFloat16 from Transformer)
            # We request 'latents' so we can handle the VAE decode manually in Float32
            output = self.pipe(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_frames=num_frames,
                num_inference_steps=num_steps,
                generator=torch.Generator().manual_seed(seed),
                output_type="latents" # Return raw latents
            )
            
            latents = output.frames[0] # [C, F, H, W] or [B, C, F, H, W]
            
            # 2. Manual Cast to Float32
            # This fixes the "Input type (BF16) and bias type (Float) should be the same" error
            print(f"DEBUG: Casting latents from {latents.dtype} to Float32...")
            latents = latents.to(dtype=torch.float32)

            # 3. Manual Decode with VAE
            # Standard Diffusers VAE decoding logic:
            # Latents are usually scaled; we must unscale them.
            # LTX VAE uses the standard scaling factor (usually 0.18215 or similar)
            if hasattr(self.pipe.vae.config, "scaling_factor"):
                latents = latents / self.pipe.vae.config.scaling_factor

            print("Decoding latents with VAE (Float32)...")
            with torch.no_grad():
                video_tensor = self.pipe.vae.decode(latents.unsqueeze(0)).sample

            # 4. Post-process to PIL/Video
            # LTX pipeline has a video_processor
            print("Post-processing video...")
            video = self.pipe.video_processor.postprocess_video(video_tensor, output_type="pil")[0]

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