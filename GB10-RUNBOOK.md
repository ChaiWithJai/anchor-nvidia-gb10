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

The launcher validates the host and local artifacts, starts MongoDB and
Nemotron, performs a cloned-voice warmup, and runs the full clinical call test.
Startup can take several minutes while vLLM loads five NVFP4 shards.

## Inspect

```bash
docker compose -f compose.nvidia.yml ps
docker compose -f compose.nvidia.yml logs --tail 100 nemotron
docker compose -f compose.nvidia.yml logs --tail 100 digital-twin
curl --fail http://127.0.0.1:8100/api/status
nvidia-smi
```

`/api/status` is ready only when MongoDB responds, Nemotron lists the pinned
model, and CSM has generated a valid 24 kHz WAV on CUDA.

Open both working interfaces:

- Clinician console: <http://127.0.0.1:8100/>
- Patient call: <http://127.0.0.1:8100/patient>

The patient flow uses a consented synthetic record. A completed or escalated
call appears in the clinician console without a refresh of the underlying
workload.

## Attach the local agent runtime

The application is complete without an agent hook: alerts are persisted first
and report `not-configured`. To demonstrate the competition's two-of-three
agent stack, attach OpenClaw inside NVIDIA OpenShell using
[OPENSHLL.md](OPENSHLL.md). The validated route is:

```text
Anchor container -> private bearer hook -> OpenClaw 2026.5.27
  -> inference.local -> OpenShell 0.0.106 -> loopback Nemotron on GB10
```

The hosted NemoClaw plugin is disabled in this configuration. OpenShell forces
the model route to the local Nemotron provider and denies general model egress.
`/api/status` reports `agent_runtime.configured: true` only when both the hook
URL and its separate bearer token are present.

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

- Local MongoDB, CSM, and Nemotron readiness is true.
- Shared mode is enabled.
- The HTTPS login page and both application routes are reachable.
- An anonymous private API request returns HTTP 401.
- The full verifier can be run through the HTTPS URL after authentication.

The public URL changes whenever the proxy container is recreated. Stop it with:

```bash
docker compose -f compose.nvidia.yml --profile share stop share-proxy
```

Cloudflare transports remote browser traffic. Inference and persistence stay
on the GB10, but request content is no longer confined to the local network.

## Prove MongoDB is the system of record

MongoDB is isolated on the Compose network and has no host port. Inspect it
through the service container:

```bash
docker compose -f compose.nvidia.yml exec mongodb sh -lc \
  'mongosh --quiet --username "$MONGO_INITDB_ROOT_USERNAME" \
    --password "$MONGO_INITDB_ROOT_PASSWORD" \
    --authenticationDatabase admin anchor \
    --eval "printjson({patients:db.patients.countDocuments(),calls:db.calls.countDocuments(),alerts:db.alerts.countDocuments(),audit:db.audit_events.countDocuments()})"'
```

The named `mongo-data` volume preserves clinic records across restarts.
Deleting that volume destroys the synthetic demo records and is not part of the
normal stop procedure.

## Stop

```bash
docker compose -f compose.nvidia.yml down
```

`docker compose down` retains `mongo-data`; do not add `--volumes`.
