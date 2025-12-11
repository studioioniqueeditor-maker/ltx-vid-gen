<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# deep research on how to prompt the ltx 0.9.8 13b best for Image + Text to Video tasks to get maximum controllability for very minor movements - like camera zoom/dolly etc + small arm movement etc

Excellent! I have comprehensive research. Now let me create a detailed guide based on all the information gathered.

## Deep Research: Optimized Prompting for LTX 0.9.8 13B - Image-to-Video with Fine-Grained Motion Control

### Core Prompting Philosophy for LTX 0.9.8

**The fundamental principle for maximizing controllability with LTX 0.9.8 is structural clarity over verbose descriptions.** The model tokenizes and respects discrete semantic chunks, meaning you should format prompts like a director's shot list rather than flowing narrative prose. This architecture-aware approach directly improves motion coherence, reduces drift, and enables precise micro-movement control.[^1][^2][^3]

### Six-Part Prompt Structure for Maximum Controllability

The optimal structure for fine-grained motion control follows this hierarchical format:

**[Scene Anchor] : [Subject + Action] : [Camera + Lens] : [Visual Style] : [Motion Intent] : [Guardrails]**

This segmentation is critical because LTX 0.9.8 leverages the T5XXL text encoder, which performs substantially better with clearly delineated clauses. Each colon-separated section gets processed with greater fidelity than run-on descriptions.[^4][^5]

### Part 1: Scene Anchor with Stationary References

For **very minor movements** like camera zoom or dolly, you must establish fixed reference points. This prevents the model from reinterpreting your entire frame during motion.[^6][^7][^3]

**Structure:** "Scene: [environment description with foreground anchor], [stationary element], [depth reference]"

**Examples:**

- "Scene: Office desk with laptop in sharp foreground (stationary), wall calendar in background, wooden chair to left"
- "Scene: Forest floor close-up with moss and roots foreground (anchored), stationary rocks, towering trees in soft focus distance"
- "Scene: Product on white surface (fixed), shadow cast to right side (unchanging), neutral background"

**Why this works:** Anchoring foreground elements prevents parallax collapse and gives the model spatial references to preserve during motion. It also stabilizes background elements that shouldn't drift.[^7][^6]

### Part 2: Subject + Action with Micro-Motion Vocabulary

For **subtle movements**, use **precise, kinetic motion verbs** rather than conceptual language. The distinction between "gently moves" versus "imperceptibly shifts" matters significantly.[^8]

**Micro-Motion Vocabulary for Small Gestures:**

- "Subtle arm raise" (not "arms move")
- "Gentle index finger curl" (not "hand motion")
- "Barely perceptible chin tilt" (for micro-expressions)
- "Soft shoulder shift" (minimal translation)
- "Eyelid flutter" (blinking—inherently micro)
- "Lip corner twitch" (micro-expression equivalent)[^7]

**For breathing/living movement:**

- "Shallow breathing" (chest expansion, minimal)
- "Ambient chest rise-fall" (steady, not exaggerated)
- "Slight blink pattern" (natural but controlled)

**Critical principle:** Avoid "flowing," "drifting," or "swaying" for micro-movements—these trigger larger motion trajectories. Reserve those for intentional scene motion.[^8]

### Part 3: Camera Movement Keywords for Zoom/Dolly/Subtle Push

This is where LTX 0.9.8's improvements shine. Use **explicit distance and speed modifiers** to constrain motion magnitude.[^3][^6]

**Zoom vs. Dolly Distinction:**

- **Zoom:** "Camera focal length increases 35mm to 50mm" (changes perspective, stays in place)—flattens depth, faster render time, ~38 seconds for 6-second clip at 1080p
- **Dolly In:** "Camera physically moves forward 0.5 meters" (maintains parallax, more cinematic)—preserves depth relationships, ~45 seconds for 6-second clip at 1080p[^6]

**Micro-Camera Movement Parameters:**

- **Subtle push:** "Slow push-in 0.3 meters over 5 seconds" (not "over the clip")
- **Minimal zoom:** "Gentle focal length shift from 28mm to 35mm" (constraint: stay under 15mm swing)
- **Restricted pan:** "Micro pan right 2°, minimal head rotation follow" (measurable angle)
- **Rack focus:** "Focus pull from foreground product to background (slight, ~0.5 second transition)" (not full rack)

**For handheld-style stability:**

- "Tripod-locked, zero drift" (prevents jitter for fine details)
- "Minimal micro-jitter if handheld" (adds texture without chaos)
- "Steady dolly, 180° shutter equivalent" (implies natural motion blur)[^3]

**Distance specificity matters:** Tests show "push-in 2 meters" maintains linear scale changes better than vague "move closer." For micro-movements, use fractions: "push-in 0.25 meters," "shift right 0.5 meters."[^3]

### Part 4: Visual Style + Lighting Preservation

Micro-movements often suffer from lighting shifts and texture degradation. Pin these down.[^7][^3]

**Static lighting anchor:**

- "Consistent warm overhead lighting (unchanged)"
- "Key light from left maintained, no shift"
- "Soft natural diffusion (no contrast change)"

**Avoid high-frequency patterns** that create moiré or distortion during subtle motion:[^3]

- Instead of: "Detailed brick wall texture"
- Use: "Soft neutral background, minimal texture, slight bokeh"


### Part 5: Motion Intent \& Timing Cues

**Critical for fine-grained control—specify motion speed and timing explicitly.**[^7][^3]

**Speed descriptors for subtle motion:**

- "Imperceptibly slow" (CFG interpretation: ~0.5 speed multiplier)
- "Glacial pace" (intentionally minimal)
- "Real-time speed" (natural human/object movement, no slow-mo)
- "One second for [action]" (explicit timing)

**Timing anchors for multi-action sequences:**

```
"At 0s: subject stationary / at 2s: gentle finger raise / 
at 4s: arm returns / at 6s: final static pose"
```

**Frame rate intent:**

- "24 fps cinematic cadence with natural motion blur" (smooths micro-movements)
- "48 fps for precision detail (avoid for heavy motion)"


### Part 6: Guardrails \& Negative Instructions

**Negative prompts must be specific to motion, not generic.** Generic negatives like "blurry, low quality" waste prompt tokens on irrelevant concerns.[^5][^9]

**Motion-specific negatives:**

```
"no sudden jumps, no erratic motion, no morphing, 
no temporal inconsistency, no background drift, 
no parallax collapse, avoid motion smear artifacts"
```

**For anchored elements:**

```
"foreground stays locked, background stationary relative to depth, 
no camera wobble, no jitter beyond stated intent"
```

**Avoid stating what you don't want as positive instruction.** Instead of "no fast movement," say "imperceptibly slow" in the positive section.

***

## Technical Parameter Optimization for LTX 0.9.8 13B

### Guidance Parameters: CFG vs. STG

**CFG (Classifier-Free Guidance):** Controls prompt adherence. For subtle motion: **CFG 5.0–7.0**.[^10][^11][^12][^13]

- Lower values (5.0) = more natural, less prompt-bound motion
- Higher values (7.0–9.0) = stricter prompt following, can create unnatural micro-movements

**STG (Spatiotemporal Guidance):** Advanced skip-layer guidance that refines movement by overriding CFG at specific layers, reducing morphing and flickering on character/object details.[^11][^14]

- Best layer to target: **Layer 14** (model-dependent, test 10–16 range)
- Scale value: **1.0–2.0** (1.0 = subtle refinement, 2.0 = aggressive detail preservation)
- CFG must remain >1.0 when using STG override

**Recommended for micro-movements:** Use STG with CFG 6.0 + STG Scale 1.0 + Layer 14 override. This preserves micro-expressions and small gestures without morphing.[^14][^11]

### Inference Steps \& Denoising Strategy

**For fine-grained control:**

- First pass: **8 inference steps** (distilled model) or **20 steps** (full model) at downscaled resolution
- Second pass: **Denoise strength 0.4** with upsampled latents + **10 inference steps** total (effectively 4 new inference steps)[^15]
- **decode_timestep: 0.05** (controls final VAE decode noise—use 0.05 for consistency)
- **image_cond_noise_scale: 0.025** (initial frame conditioning noise—keep at 0.025 for tight reference adherence)[^15]


### Seed Management for Reproducibility

**Fixed seed + fixed prompt = consistent output.** For subtle variations on locked motion:[^14]

Option 1: Fix seed + prompt, regenerate (produces scene variation within same camera path)
Option 2: Inject random 32-bit hex code to prompt end while keeping seed fixed (produces character variation, maintains motion)[^14]

***

## Advanced: IC LoRA (In-Context LoRA) for Pose/Depth Control

LTX 0.9.8 includes built-in IC LoRA adapters for three control modalities:[^16][^17][^4]

**1. Pose Control (ICLoRA-pose):** Constrains subject movement via pose keyframes

- Most effective for arm raises, finger movements, head tilts
- Inject pose guidance at chunk boundaries (every ~15 frames for 30+ second sequences)[^2][^16]
- Use depth maps for skeletal references

**2. Depth Control (ICLoRA-depth):** Preserves spatial parallax during dolly/push

- Essential for camera zoom/dolly micro-movements
- Prevent parallax collapse with depth anchoring at frame 0
- Re-inject depth map every 15–20 frames for long-form consistency[^2][^16]

**3. Canny Edge Control:** Maintains compositional geometry

- Useful for preventing unwanted edge warping during subtle camera pan/tilt
- Lower Canny threshold for detailed control, higher for loose guidance[^18][^19]

**Practical workflow:** For a 0.5-meter camera dolly on a product shot:

1. Extract depth map from reference image
2. Apply ICLoRA-depth at frame 0 with scale 0.7–0.8
3. Re-apply at frame 60 (for ~2.5 second segment) with adjusted depth scale
4. Pair with "camera physically moves forward 0.5 meters" prompt in Camera section

***

## Multi-Prompt Timeline Control for Micro-Motion Sequences

LTX 0.9.8 supports **multi-prompt provider** with timeline-based segmentation. This is critical for controlling when micro-movements occur.[^20][^1][^2]

**Structure:**

```
"0s-2s: subject stationary, camera locked / 
2s-4s: gentle finger curl at frame timing 2.0s / 
4s-6s: arm returns to rest position slowly / 
6s-end: final pose held"
```

**Timing specificity:**

- Use exact second markers: "at 1.5s," "by frame 24," "starting 2.0 seconds"
- Avoid ambiguous duration words ("soon," "then," "after")
- Separate each timeline segment with forward slash or explicit colon

**Common failure mode:** If micro-movements diverge between prompts, add **continuity anchors**—"subject position unchanged from previous segment" or "maintain arm angle from 0-2s section."[^4]

***

## Prompt Engineering Examples for Common Micro-Motions

### Example 1: Gentle Camera Zoom on Product

```
Scene: Sleek wireless headphones on black matte surface, 
white studio backdrop (unchanging), soft box lighting from left (fixed)

Subject: Headphones remain stationary throughout

Camera: Slow 35mm to 50mm focal length shift over 4 seconds, 
tripod-locked on center product (no panning)

Style: Commercial product photography, soft shadows, 
neutral color palette, sharp detail on headphones

Motion: Imperceptibly slow zoom revealing headphone texture, 
focus remains on earcup details, no depth-of-field shift

Guardrails: no background blur, surface position locked, 
lighting consistent, avoid motion artifacts at edge of frame
```


### Example 2: Micro-Expression (Subtle Smile)

```
Scene: Close-up human face, neutral background (soft bokeh), 
consistent warm window lighting from camera-left (unchanged throughout)

Subject: Person's face stationary except for mouth corners, 
subtle smile begins at 1s and peaks at 3s

Camera: Locked static 50mm portrait lens, absolutely no drift or pan, 
zero head movement

Style: Soft natural lighting, cinematic shallow depth-of-field, 
skin tones warm and natural

Motion: Lip corners rise very slightly (mouth closed), 
duration 2 seconds for smile onset, imperceptibly gentle

Guardrails: avoid morphing, no cheek bulge, eyes unchanged, 
eyebrows stay level, skin remains smooth (no texture shift)
```


### Example 3: Arm Micro-Raise (0.3m vertical distance)

```
Scene: Person at desk, wooden table surface (anchored in frame), 
neutral wall background with framed picture (unmoved)

Subject: Right arm raises from resting position on desk to 
shoulder height, hand remains open and relaxed

Camera: Medium shot (waist to head), locked tripod position 
with 35mm lens, zero camera motion

Style: Office environment, warm desk lamp lighting (unchanged), 
natural skin tones

Motion: Arm rises slowly over 2.5 seconds with natural gravitational easing, 
elbow leads slightly, shoulder rises minimally (less than 5% of arm length)

Guardrails: no jerking, arm maintains shape integrity, 
hand doesn't rotate, sleeve fabric moves naturally but doesn't distort
```


### Example 4: Dolly-In (0.3m forward motion) on Subject

```
Scene: Person in forest, moss-covered ground and roots in sharp foreground 
(remain stationary and locked), towering trees blurred in background

Subject: Person breathing naturally with slight chest rise, 
face expression neutral and unchanging

Camera: Handheld-style dolly forward 0.3 meters over 4 seconds 
maintaining focus on person's eyes, minimal subtle micro-jitter controlled, 
steady 24fps

Style: Nature documentary aesthetic, soft diffused forest light 
(shadows stay consistent), deep forest focus

Motion: Camera travels forward gradually with parallax showing depth, 
foreground moss elements separate from midground as camera pushes

Guardrails: avoid sudden focus shifts, foreground anchors don't move, 
background remains coherent, parallax preserved throughout
```


***

## Practical Troubleshooting: Why Micro-Movements Fail

| Problem | Root Cause | Solution |
| :-- | :-- | :-- |
| Zoom appears as pan/drift | Camera section too vague | Explicitly state "focal length shift" not "camera move" |
| Micro-expression morphs into full expression | No anchoring of adjacent features | Add "eyebrows unchanged, cheeks static" |
| Background drifts during dolly | No foreground anchor | Specify "foreground stationary, foreground elements locked in frame" |
| Jitter/wobble in subtle motion | STG parameters too aggressive | Reduce STG scale to 0.5–0.8, increase CFG to 6.5+ |
| Motion stops mid-sequence | Prompt degradation beyond 15–20s | Use multi-prompt timeline, re-anchor every 15 frames |
| Arm raises but body shifts | No reference skeleton pose | Inject pose control with IC LoRA-pose at frame 0 |


***

## Hardware \& Performance Notes

**13B distilled model requirements for fine-grained control:**

- **Minimum:** 24GB VRAM (4090, 5090, A6000)
- **Optimal resolution:** 720×1280 (under limit, maximizes detail preservation)
- **Ideal frame count:** 96–129 frames (4–5 seconds at 24fps)
- **First pass downscale:** 2/3 reduction (480×853), then upscale; reduces VRAM spike
- **Inference time:** ~8–12 seconds for high-quality single generation[^21][^22][^4]

**T5XXL text encoder precision:**

- FP16 recommended (better quality than FP8, slightly more VRAM)
- FP8 acceptable for speed with Q8 LoRA loader node for proper weight handling[^4]

***

## Summary: Prompting Checklist for Maximum Micro-Movement Controllability

1. **Use colon-separated six-part structure** (scene anchor : subject+action : camera : style : motion intent : guardrails)
2. **Anchor foreground + background explicitly** with words like "stationary," "locked," "unchanging"
3. **Choose precise camera vocabulary:** "focal length shift" vs. "dolly forward [distance]"
4. **Specify motion speed:** "imperceptibly slow," "one second for [action]"
5. **Use STG with Layer 14** override at Scale 1.0, paired with CFG 6.0
6. **Apply IC LoRA guidance** (depth/pose) every 15 frames for longer sequences
7. **Multi-prompt timeline** with explicit timestamps for complex motion sequences
8. **Negative prompts** focus on motion artifacts, not generic quality issues
9. **Test on shorter sequences** (10–20 seconds) to validate micro-motion fidelity
10. **Use fixed seed + hex code injection** for reproducible variations on locked movements

**Key insight:** LTX 0.9.8's strength lies not in generating large, dynamic motion, but in the precision with which it can constrain motion to specified micro-movements when prompts are structurally clear and anchored with spatial reference points.[^1][^4][^3]
<span style="display:none">[^100][^101][^102][^103][^104][^105][^106][^107][^108][^109][^110][^111][^112][^113][^114][^115][^116][^117][^118][^119][^120][^121][^122][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39][^40][^41][^42][^43][^44][^45][^46][^47][^48][^49][^50][^51][^52][^53][^54][^55][^56][^57][^58][^59][^60][^61][^62][^63][^64][^65][^66][^67][^68][^69][^70][^71][^72][^73][^74][^75][^76][^77][^78][^79][^80][^81][^82][^83][^84][^85][^86][^87][^88][^89][^90][^91][^92][^93][^94][^95][^96][^97][^98][^99]</span>

<div align="center">⁂</div>

[^1]: https://www.youtube.com/watch?v=E5czKaoYaL4

[^2]: https://www.youtube.com/watch?v=E5czKaoYaL4\&vl=it

[^3]: https://skywork.ai/blog/ai-video/ltx-2-prompts-guide-4k-examples/

[^4]: https://syntheticlabs.xyz/2025/07/23/ltx-video-long-form-ai/

[^5]: https://www.eachlabs.ai/ai-models/ltx-video

[^6]: https://skywork.ai/blog/ltx-2-camera-prompts-shot-editor/

[^7]: https://www.lovart.ai/blog/ai-video-prompts

[^8]: https://help.runwayml.com/hc/en-us/articles/39789879462419-Gen-4-Video-Prompting-Guide

[^9]: https://huggingface.co/spaces/emilalvaro/LTX-Video-Playground/commit/9d5309acfb9559cc84c0c4ed6ace0bd647a7f598

[^10]: https://www.youtube.com/watch?v=peSg06CzMdk

[^11]: https://www.youtube.com/watch?v=1QKntG7pSH8

[^12]: https://getimg.ai/guides/interactive-guide-to-stable-diffusion-guidance-scale-parameter

[^13]: https://completeaitraining.com/course/comfyui-course-ep-25-ltx-video-fast-ai-video-generator-model/

[^14]: https://www.youtube.com/watch?v=KZixJo5a8us

[^15]: https://huggingface.co/docs/diffusers/main/en/api/pipelines/ltx_video

[^16]: https://blog.fal.ai/new-ltxv-0-9-8-model-live-on-fal/

[^17]: https://github.com/Lightricks/ComfyUI-LTXVideo/blob/master/README.md

[^18]: https://www.youtube.com/watch?v=Bq7PT1qZ-_s

[^19]: https://www.youtube.com/watch?v=mZ1Rpjej54c

[^20]: https://www.youtube.com/watch?v=E5czKaoYaL4\&vl=ja

[^21]: https://stable-diffusion-art.com/ltxv-13b/

[^22]: https://huggingface.co/Lightricks/LTX-Video-0.9.8-13B-distilled

[^23]: https://arxiv.org/abs/2412.04512

[^24]: https://dl.acm.org/doi/10.1145/3675395

[^25]: https://aclanthology.org/2023.artofsafety-1.2

[^26]: https://link.springer.com/10.1007/s10278-025-01530-6

[^27]: https://www.semanticscholar.org/paper/2069aaaa281eb13bcd9330fc4d43f24f6b436a53

[^28]: https://link.springer.com/10.1007/978-981-97-2262-4_5

[^29]: https://www.frontiersin.org/articles/10.3389/frai.2024.1514896/full

[^30]: http://medrxiv.org/lookup/doi/10.1101/2024.03.21.24304667

[^31]: https://ieeexplore.ieee.org/document/10806871/

[^32]: https://arxiv.org/abs/2402.15061

[^33]: https://arxiv.org/pdf/2210.02441.pdf

[^34]: http://arxiv.org/pdf/2406.06608.pdf

[^35]: https://arxiv.org/pdf/2312.16171.pdf

[^36]: https://arxiv.org/pdf/2502.16137.pdf

[^37]: http://arxiv.org/pdf/2408.09365.pdf

[^38]: http://arxiv.org/pdf/2412.04512.pdf

[^39]: https://arxiv.org/pdf/2405.05418.pdf

[^40]: http://arxiv.org/pdf/2404.16873.pdf

[^41]: https://www.youtube.com/watch?v=rE1DfAhB_jc

[^42]: https://huggingface.co/docs/diffusers/en/api/pipelines/ltx_video

[^43]: https://ltx.studio/blog/mastering-camera-motion-gen-space

[^44]: https://arxiv.org/pdf/2412.02700v2.pdf

[^45]: https://arxiv.org/html/2503.06508v1

[^46]: https://arxiv.org/html/2503.15973

[^47]: https://arxiv.org/pdf/2308.04828.pdf

[^48]: https://arxiv.org/html/2407.03179v1

[^49]: https://arxiv.org/pdf/2401.08559.pdf

[^50]: https://arxiv.org/pdf/2212.04821.pdf

[^51]: https://arxiv.org/html/2502.06428v1

[^52]: https://pypi.org/project/ltx-video/

[^53]: https://www.youtube.com/watch?v=9uwp-xksCAc

[^54]: https://github.com/Lightricks/ComfyUI-LTXVideo

[^55]: https://www.reddit.com/r/comfyui/comments/1m5tsik/ltxvideo_098_2b_distilled_i2v_small_blazing_fast/

[^56]: https://www.studiobinder.com/camera-shots/camera-movements/dolly-zoom-shot/

[^57]: https://www.semanticscholar.org/paper/904f622f1427bd2256c1b834fc377e61a62ed7fe

[^58]: http://www.mededportal.org/doi/10.15766/mep_2374-8265.10712

[^59]: https://www.semanticscholar.org/paper/44c556f805a30282d8638cb9837de24852682d05

[^60]: https://www.semanticscholar.org/paper/91acff91b8f0a86109036b363a758e8c31c7adda

[^61]: http://peer.asee.org/26154

[^62]: https://www.informingscience.org/Publications/1795

[^63]: https://www.semanticscholar.org/paper/12e9c98e7eb818a21c12d8497ef6954f04f90863

[^64]: https://www.semanticscholar.org/paper/e175d1dac35f2622949c638a7436766eb0550baa

[^65]: https://www.semanticscholar.org/paper/a40ae5b19151c783f7e33809744ae68e07a9181d

[^66]: https://journals.sagepub.com/doi/10.1111/imre.12277

[^67]: https://arxiv.org/pdf/2310.15324.pdf

[^68]: https://arxiv.org/html/2312.17117v1

[^69]: http://arxiv.org/pdf/2405.00983.pdf

[^70]: http://arxiv.org/pdf/2309.04379v1.pdf

[^71]: https://arxiv.org/pdf/2408.08780v1.pdf

[^72]: https://arxiv.org/html/2412.15156v1

[^73]: https://www.reddit.com/r/StableDiffusion/comments/1h2z4lx/making_a_more_detailed_prompt_for_ltx_video/

[^74]: https://www.reddit.com/r/StableDiffusion/comments/1h26okm/ltxvideo_tips_for_optimal_outputs_summary/

[^75]: https://www.semanticscholar.org/paper/f417e28e05acb599aff7f42fd9f1549d35821c28

[^76]: https://www.cambridge.org/core/services/aop-cambridge-core/content/view/0963736A0B2738179735FFDE4E7D1EFB/S0263574723000255a.pdf/div-class-title-analytical-expression-of-motion-profiles-with-elliptic-jerk-div.pdf

[^77]: https://www.mdpi.com/2504-446X/7/12/706/pdf?version=1702457440

[^78]: http://arxiv.org/pdf/2409.01465.pdf

[^79]: https://www.mdpi.com/2076-3417/10/9/3010/pdf

[^80]: http://arxiv.org/pdf/2403.05878.pdf

[^81]: https://www.mdpi.com/2076-3417/13/22/12115/pdf?version=1699365528

[^82]: http://arxiv.org/pdf/2303.00817.pdf

[^83]: https://arxiv.org/pdf/2411.19144.pdf

[^84]: https://arxiv.org/html/2501.00103v1

[^85]: https://fal.ai/models/fal-ai/ltx-video-13b-distilled/multiconditioning

[^86]: https://cloudernative.com/ai-models/model/lightricks/ltx-video

[^87]: https://ltx.studio

[^88]: https://arxiv.org/html/2406.17758v2

[^89]: https://arxiv.org/html/2411.10836v1

[^90]: https://arxiv.org/html/2406.19680v1

[^91]: https://arxiv.org/pdf/2311.11325.pdf

[^92]: http://arxiv.org/pdf/2312.04086.pdf

[^93]: https://arxiv.org/html/2403.13900v2

[^94]: https://arxiv.org/abs/2311.12631

[^95]: https://www.studiobinder.com/blog/ultimate-guide-to-camera-shots/

[^96]: https://www.nfi.edu/camera-movement-terms/

[^97]: https://letsenhance.io/blog/all/ai-video-camera-movements/

[^98]: https://www.storyblocks.com/resources/tutorials/7-basic-camera-movements

[^99]: https://www.youngurbanproject.com/sora-prompts-for-ai-video-generation/

[^100]: http://arxiv.org/pdf/2409.14595.pdf

[^101]: https://arxiv.org/pdf/2408.01890v1.pdf

[^102]: http://arxiv.org/pdf/2411.02063.pdf

[^103]: https://arxiv.org/pdf/2411.01537v1.pdf

[^104]: http://arxiv.org/pdf/2404.08634.pdf

[^105]: https://arxiv.org/pdf/2307.08691.pdf

[^106]: https://arxiv.org/pdf/2503.23174.pdf

[^107]: http://arxiv.org/pdf/2402.05602.pdf

[^108]: https://www.promptlayer.com/models/t5xxl

[^109]: https://github.com/mcmonkeyprojects/SwarmUI/blob/master/docs/Video Model Support.md

[^110]: https://civitai.com/models/995093/ltx-image-to-video-with-stg-caption-and-clip-extend-workflow

[^111]: https://arxiv.org/html/2506.08456v1

[^112]: https://www.runcomfy.com/comfyui-nodes/ComfyUI-LTXTricks/ltx-attn-override

[^113]: https://arxiv.org/html/2311.17009v2

[^114]: http://arxiv.org/pdf/2403.18915.pdf

[^115]: http://arxiv.org/pdf/2406.04277.pdf

[^116]: http://arxiv.org/pdf/2411.10332.pdf

[^117]: https://imotions.com/blog/learning/research-fundamentals/facial-expressions-a-complete-guide/

[^118]: https://openreview.net/pdf?id=O82UIq0oID

[^119]: https://study.com/learn/lesson/micro-expressions-definition-examples.html

[^120]: https://helpx.adobe.com/in/premiere/desktop/add-video-effects/control-effects-and-transitions-using-keyframes/control-effect-changes-using-keyframe-interpolation.html

[^121]: https://pmc.ncbi.nlm.nih.gov/articles/PMC8763852/

[^122]: https://www.cometapi.com/kling-2-6-full-analysis-how-to-use-and-prompt/

