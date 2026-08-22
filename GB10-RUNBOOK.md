# GB10 runbook

## Prerequisites

- ARM64 Ubuntu host with an NVIDIA GB10
- Docker Engine, Compose, and NVIDIA Container Toolkit
- T7 bundle mounted at `/media/dell/T7/hackathon-2026-08-22`
- `nvcr.io/nvidia/vllm:26.05.post1-py3` available locally or pullable from NGC

## Start and prove the workload

```bash
cd /home/dell/anchor-nvidia-gb10
export HACKATHON_BUNDLE=/media/dell/T7/hackathon-2026-08-22
./scripts/run-nvidia
```

Expected final line:

```text
Anchor NVIDIA GB10 ready: http://127.0.0.1:8100/
```

The launcher validates the host and local artifacts, builds the CUDA app,
starts Nemotron, performs a cloned-voice warmup, and runs the end-to-end call
test. Startup can take several minutes while vLLM loads five NVFP4 shards.

## Inspect

```bash
docker compose -f compose.nvidia.yml ps
docker compose -f compose.nvidia.yml logs --tail 100 nemotron
docker compose -f compose.nvidia.yml logs --tail 100 digital-twin
curl --fail http://127.0.0.1:8100/api/status
nvidia-smi
```

`/api/status` is ready only when Nemotron lists the pinned model and CSM has
already generated a valid 24 kHz WAV on CUDA.

## Stop

```bash
docker compose -f compose.nvidia.yml down
```

The named `digital-twin-data` volume preserves call memory across restarts.
