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

## Temporary team URL

```bash
export HACKATHON_BUNDLE=/media/dell/T7/hackathon-2026-08-22
export ANCHOR_DEMO_ACCESS_KEY='choose-a-private-team-code'
./scripts/share-nvidia
```

The access code must contain at least 12 characters. The root URL presents a
login form; all private API routes require the resulting signed, HttpOnly
cookie. `/api/status` remains public for health checks and contains no call or
resident data. The raw Nemotron port is loopback-only.

Verification performed by the launcher:

- Local CSM and Nemotron readiness is true.
- Shared mode is enabled.
- The HTTPS login page is reachable.
- An anonymous private API request returns HTTP 401.

The public URL changes whenever the proxy container is recreated. Stop it with:

```bash
docker compose -f compose.nvidia.yml --profile share stop share-proxy
```

Cloudflare transports remote browser traffic. Inference and persistence stay
on the GB10, but request content is no longer confined to the local network.

## Stop

```bash
docker compose -f compose.nvidia.yml down
```

The named `digital-twin-data` volume preserves call memory across restarts.
