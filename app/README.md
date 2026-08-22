# Application

FastAPI serves the digital-twin call API and static browser UI. The container is
built by the root `compose.nvidia.yml`; direct host execution is not supported
because cloned speech requires the NVIDIA CUDA runtime and local CSM weights.

Key endpoints:

- `GET /api/status`
- `POST /api/calls`
- `POST /api/calls/{id}/turn`
- `POST /api/calls/{id}/end`
- `POST /api/tts`
- `GET /api/residents/{id}/memory`
