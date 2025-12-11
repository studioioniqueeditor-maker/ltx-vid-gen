"""
LTX Video 13B Image-to-Video Generator
Optimized for RunPod A40 @ 720p
"""

import torch
import os
import time
import argparse
from pathlib import Path
from diffusers import LTXConditionPipeline
from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition
from diffusers.utils import export_to_video, load_image

# Configuration
MODEL_PATH = '/workspace/models/ltxv-13b-distilled'
OUTPUT_DIR = '/workspace/outputs'

# 720p settings
WIDTH = 1280
HEIGHT = 720
NUM_FRAMES = 121  # ~5 seconds at 24fps
FPS = 24
NUM_STEPS = 8  # Distilled model needs fewer steps


def load_pipeline():
    """Load LTX pipeline with optimizations"""
    print("Loading LTX Video 13B Distilled...")
    
    pipe = LTXConditionPipeline.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16
    )
    pipe.to("cuda")
    pipe.vae.enable_tiling()
    
    print("Model loaded successfully!")
    return pipe


def generate_video(pipe, image_path, prompt, output_name, seed=42):
    """Generate video from image

    Args:
        pipe: Loaded LTX pipeline
        image_path: Path to input image (local path or URL)
        prompt: Motion description prompt
        output_name: Output filename (without extension)
        seed: Random seed for reproducibility

    Returns:
        Path to generated video

    Raises:
        ValueError: If image_path is invalid or inaccessible
        Exception: If generation fails
    """
    # Validate and load input image
    # Note: URL validation should be done by caller (validation.py)
    # This is a secondary safety check
    try:
        image = load_image(image_path)
    except Exception as e:
        raise ValueError(f"Failed to load image from {image_path[:50]}...: {e}")
    
    # Create conditioning
    condition = LTXVideoCondition(
        image=image,
        frame_index=0
    )
    
    negative_prompt = "worst quality, inconsistent motion, blurry, jittery, distorted"
    
    print(f"Generating video: {output_name}")
    print(f"  Resolution: {WIDTH}x{HEIGHT}")
    print(f"  Frames: {NUM_FRAMES} (~{NUM_FRAMES/FPS:.1f}s at {FPS}fps)")
    print(f"  Prompt: {prompt[:50]}...")

    start = time.time()

    try:
        video = pipe(
            conditions=[condition],
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=WIDTH,
            height=HEIGHT,
            num_frames=NUM_FRAMES,
            num_inference_steps=NUM_STEPS,
            generator=torch.Generator().manual_seed(seed),
            output_type="pil"
        ).frames[0]
    except torch.cuda.OutOfMemoryError:
        raise Exception(
            f"GPU out of memory. Try reducing resolution or num_frames. "
            f"Current: {WIDTH}x{HEIGHT}, {NUM_FRAMES} frames"
        )
    except Exception as e:
        raise Exception(f"Video generation failed: {e}")

    elapsed = time.time() - start
    print(f"Generated in {elapsed:.1f}s")

    # Save output
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = f"{OUTPUT_DIR}/{output_name}.mp4"
        export_to_video(video, output_path, fps=FPS)
    except Exception as e:
        raise Exception(f"Failed to save video: {e}")

    print(f"Saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="LTX Video I2V Generator")
    parser.add_argument("--image", required=True, help="Input image path or URL")
    parser.add_argument("--prompt", required=True, help="Motion description prompt")
    parser.add_argument("--output", default="output", help="Output filename (no extension)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--width", type=int, default=1280, help="Output width")
    parser.add_argument("--height", type=int, default=720, help="Output height")
    parser.add_argument("--frames", type=int, default=121, help="Number of frames")
    parser.add_argument("--steps", type=int, default=8, help="Inference steps")
    args = parser.parse_args()
    
    # Update globals if custom values provided
    global WIDTH, HEIGHT, NUM_FRAMES, NUM_STEPS
    WIDTH = args.width
    HEIGHT = args.height
    NUM_FRAMES = args.frames
    NUM_STEPS = args.steps
    
    # Load and generate
    pipe = load_pipeline()
    path = generate_video(pipe, args.image, args.prompt, args.output, args.seed)
    
    print(f"\nDone! Video saved to: {path}")


if __name__ == "__main__":
    main()
