# Changelog

## 1.0.0 - 2026-08-22

- Extracted the CareLine self-call flow from `hybrid-ai-blueprints`.
- Added a self-contained NVIDIA GB10 Compose runtime.
- Pinned local Nemotron 3 Nano NVFP4 and CUDA Sesame CSM-1B execution.
- Corrected first-call self prompting, Nemotron token bounds, and CSM BF16 inputs.
- Added consent enforcement, real voice readiness, persistent memory, and a full
  call-lifecycle workload.
- Rebuilt the browser experience around outbound call states and digital-twin
  memory.
