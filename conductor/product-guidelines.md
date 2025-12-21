# Product Guidelines - LTX Video Generation Service

## Communication & Tone
*   **Documentation & Logs:** Use a developer-centric and actionable tone. Logs should provide clear context on the current state of the ML pipeline and provide actionable insights into performance or failures.
*   **Error Handling:** API error responses must be detailed and transparent. When a generation fails, include specific details about where the pipeline failed (e.g., VAE encoding, transformer denoising) to help developers debug their inputs or integration.

## Code Quality & Structure
*   **Performance-First:** Prioritize efficient GPU memory management and CUDA optimizations. The codebase should focus on minimizing overhead between the API request and the start of model inference.
*   **Internal Documentation:** Maintain heavily commented code, especially for complex ML tensor operations, pipeline scheduling, and quantization logic. Explain *why* certain parameters or model states are chosen.

## API Standards
*   **Example Documentation:** Provide simple and minimal request/response examples.
*   **Integration Readiness:** All API examples should be implementation-focused, providing code snippets (e.g., `curl`, Python) that developers can copy and use immediately.

## Visual Identity (Internal)
*   **Consistency:** Ensure that all output formats (Base64 encoding, video containers) remain consistent across model versions unless explicitly versioned in the API.
