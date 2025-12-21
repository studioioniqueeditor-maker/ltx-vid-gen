# Tutorial: Image-to-Video Inference with LTX-Video (FP8 Distilled)

This guide provides a comprehensive walkthrough for setting up and running the lightest version of the LTX-Video model: the **2B distilled FP8** version. This model is specifically designed for rapid generation with minimal VRAM requirements.

---

### 1. System Requirements
Before installation, ensure your environment meets the following specifications used for testing the codebase:
*   **Python:** 3.10.5.
*   **CUDA:** Version 12.2.
*   **PyTorch:** Version >= 2.1.2.
*   **Hardware:** An **NVIDIA Ada architecture** GPU (e.g., RTX 40-series or H100) is highly recommended to leverage the performance benefits of FP8 kernels.

---

### 2. Installation Process

#### Step A: Base Environment Setup
Clone the official repository and install the necessary dependencies for inference.

```bash
# Clone the repository
git clone https://github.com/Lightricks/LTX-Video.git
cd LTX-Video

# Create and activate a virtual environment
python -m venv env
source env/bin/activate

# Install the package with inference-specific dependencies
python -m pip install -e .[inference]
```

#### Step B: FP8 Kernel Installation (Optional/Recommended)
For maximum speed, particularly "real-time" generation on high-end cards, you should install the specialized FP8 kernels. These kernels are hosted in a separate repository; follow the specific instructions provided in the LTX-Video documentation to link them to your installation.

---

### 3. Running Inference
To use the **lightest FP8 version**, you must reference the specific configuration file: `configs/ltxv-2b-0.9.8-distilled-fp8.yaml`.

#### Method 1: Command Line Interface (CLI)
Use the `inference.py` script to generate video from a prompt and a starting image.

```bash
python inference.py \
 --prompt "A cinematic shot of a sunset over a digital ocean, vibrant purple waves" \
 --conditioning_media_paths "input_image.jpg" \
 --conditioning_start_frames 0 \
 --height 704 \
 --width 1216 \
 --num_frames 121 \
 --seed 42 \
 --pipeline_config configs/ltxv-2b-0.9.8-distilled-fp8.yaml
```

#### Method 2: Python Library Integration
You can also run the model directly within a Python script by importing the `infer` function.

```python
from ltx_video.inference import infer, InferenceConfig

# Configure and run the lightweight FP8 inference
infer(
    InferenceConfig(
        pipeline_config="configs/ltxv-2b-0.9.8-distilled-fp8.yaml", 
        prompt="Detailed description of the desired motion and scene",
        conditioning_media_paths=["input_image.jpg"],
        conditioning_start_frames=,
        height=704,
        width=1216,
        num_frames=121,
        output_path="output_video.mp4"
    )
)
```

---

### 4. Technical Optimisations & Best Practices

*   **Resolution & Frames:** The model operates most effectively on resolutions **divisible by 32** and a total frame count that follows the **$8n + 1$** rule (e.g., 121 or 257 frames).
*   **Prompt Engineering:** Focus on a single, flowing paragraph under 200 words. Describe actions, camera angles, and lighting as if you are a cinematographer writing a shot list.
*   **Guidance Scale:** For best results, keep the guidance scale between **3.0 and 3.5**.
*   **Inference Steps:** While distilled models are fast, using **40+ steps** can enhance quality, whereas **20–30 steps** are ideal for maximum speed.
*   **VRAM Efficiency:** The 2B distilled model is the most efficient choice for users with limited hardware, as it requires significantly less memory than the 13B variants.

Setting up this model is like **tuning a race car for a specific track**; while the base engine (the 2B model) is built for speed, the high-octane fuel (FP8 kernels) and the precise driving instructions (cinematographic prompts) are what allow it to achieve peak performance on the track (your GPU).