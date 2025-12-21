# Plan: Rebuild LTX Video Service from Scratch (FP8 Distilled)

## Phase 1: Environment & Clean Up [checkpoint: 4e531ad]
- [x] Task: Clean up old implementation files (preserve `conductor/`, `.gitignore`, `README.md`). 69be6c5
- [x] Task: Create `requirements.txt` with specific versions from `ltx-guide-nblm.md`. 249587a
- [x] Task: Create `Dockerfile` based on `runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04` (or similar matching CUDA 12.2 requirements) that clones the LTX-Video repo and installs dependencies. fc796ba
- [ ] Task: Conductor - User Manual Verification 'Environment & Clean Up' (Protocol in workflow.md)

## Phase 2: Model Acquisition & Network Volume [checkpoint: aba9b53]
- [x] Task: Create `download_models.py` to fetch `ltx-video-2b-v0.9.1` (or the specific distilled version) weights and the `ltxv-2b-0.9.8-distilled-fp8.yaml` config to a local directory (simulating network volume). 5666b8b
- [x] Task: Verify model download integrity locally. 7aa3baf
- [ ] Task: Conductor - User Manual Verification 'Model Acquisition & Network Volume' (Protocol in workflow.md)

## Phase 3: Inference Engine Implementation [checkpoint: 5c68fb2]
- [x] Task: Create `inference_engine.py` that interfaces with the cloned `LTX-Video` repository. b1d1dd0
    -   *Sub-task:* Implement `setup_pipeline()` to load the model from the specific path using `InferenceConfig`.
    -   *Sub-task:* Implement `generate_video()` accepting prompt, image path, and config overrides.
- [x] Task: Write a local test script `test_inference_local.py` to run a generation using `inference_engine.py` and a sample image. ae4128c
- [ ] Task: Conductor - User Manual Verification 'Inference Engine Implementation' (Protocol in workflow.md)

## Phase 4: RunPod Handler Integration [checkpoint: 646c0ea]
- [x] Task: Create `handler.py` that:
    -   Initializes the `inference_engine` on startup.
    -   Parses RunPod event input (image URL/Base64, prompt).
    -   Downloads input image to temp.
    -   Calls generation.
    -   Uploads result (or returns Base64) based on strict error handling. 10426b4
- [x] Task: Create `test_handler_local.py` to simulate a RunPod event and verify the JSON response. 10426b4
- [ ] Task: Conductor - User Manual Verification 'RunPod Handler Integration' (Protocol in workflow.md)

## Phase 5: Final Validation & Deployment Prep
- [x] Task: Create `DEPLOYMENT.md` with specific instructions for setting up the RunPod Template and Network Volume. b09d821
- [~] Task: Final code review and linting.
- [ ] Task: Conductor - User Manual Verification 'Final Validation & Deployment Prep' (Protocol in workflow.md)
