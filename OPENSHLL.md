# OpenShell + OpenClaw local handoff

This is the operator boundary for Anchor's optional clinician-agent handoff.
The clinical alert is committed to MongoDB before this path runs. A failed or
disabled handoff never changes the patient-facing safety response.

## Verified versions

- NVIDIA OpenShell CLI and gateway: `0.0.106`
- OpenClaw in the offline T7 sandbox: `2026.5.27`
- Local model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`
- OpenClaw plugins: `memory-core` only
- OpenClaw tools: `minimal` profile with an empty allowlist

The T7 sandbox contains a NemoClaw extension, but it is disabled for this demo
because its banner names a hosted endpoint. The competition allows two of the
three components; Anchor uses OpenShell and OpenClaw with a forced local model
route.

## Trust boundary

Keep all three listeners private:

- Nemotron is published on host loopback only.
- A TCP proxy binds the same service only to the `openshell-docker` bridge.
- OpenClaw is forwarded only to the Anchor Compose bridge.

Do not replace either bridge bind with `0.0.0.0`. The public Cloudflare route
terminates at the Anchor application and never exposes OpenClaw or Nemotron.
Use synthetic patient records only.

## Configure the inference route

Bind the loopback model to the OpenShell bridge only. Determine that bridge's
gateway with `docker network inspect openshell-docker`, then run:

```bash
python3 scripts/private-tcp-proxy.py \
  --listen-host "$OPENSHELL_BRIDGE_GATEWAY" \
  --listen-port 18000 --target-host 127.0.0.1 --target-port 18000
```

Start the OpenShell gateway with its Docker driver and sandbox JWT enabled,
following the vendor guide in the T7 bundle. Then register the endpointless
OpenAI-compatible profile:

```bash
openshell provider profile import --file config/openshell-openai-local.yaml
openshell provider create \
  --name anchor-local-nemotron \
  --type openai \
  --credential OPENAI_API_KEY=local-only \
  --config OPENAI_BASE_URL="$ANCHOR_PRIVATE_NEMOTRON_URL"
openshell inference set \
  --provider anchor-local-nemotron \
  --model nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4
```

`ANCHOR_PRIVATE_NEMOTRON_URL` must be an HTTP `/v1` endpoint reachable by the
gateway and sandbox but not the venue network. `openshell inference set` must
list the validated `/v1/chat/completions` endpoint before continuing.

Create the sandbox from the offline T7 OpenClaw image. Configure OpenClaw to:

- use `https://inference.local/v1` and an 8,192-token context;
- use a 256-token output cap, no tools, and an empty workspace;
- load only `memory-core`;
- enable `/hooks/wake` with a distinct random 64-character token;
- reject request-selected session keys and allow only agent `main`.

Forward OpenClaw's loopback port to the Anchor Compose bridge, not publicly:

```bash
openshell forward service anchor-clinician \
  --target-port 18789 \
  --local "$ANCHOR_COMPOSE_GATEWAY:18790"
```

Set the application variables and recreate only `digital-twin`:

```bash
export CARELINE_OPENCLAW_WAKE_URL="http://$ANCHOR_COMPOSE_GATEWAY:18790/hooks/wake"
export CARELINE_OPENCLAW_HOOK_TOKEN='the-separate-random-hook-token'
docker compose -f compose.nvidia.yml up -d --no-deps --force-recreate digital-twin
```

Never commit the hook token. Keep its file owner-readable only.

## Prove the route

```bash
openshell status
openshell inference get
openshell sandbox get anchor-clinician
curl --fail http://127.0.0.1:8100/api/status
CARELINE_BASE_URL=http://127.0.0.1:8100 python3 scripts/verify-nvidia.py
```

Required evidence:

- OpenShell is `Connected` and the sandbox is `Ready`.
- The inference provider and model are the local Anchor route.
- OpenClaw starts with one plugin, `memory-core`.
- The verifier reports `OpenClaw delivery is delivered`.
- The MongoDB alert contains the same `agent_delivery.status`.
- OpenClaw's trajectory ends with `finalStatus: success` and provider
  `inference`; OpenShell logs show the inference route is locally executed.

A hook HTTP 200 proves acceptance, not clinical review. Anchor therefore says
"flagged for on-call clinician review" and never claims that a clinician was
notified. OpenClaw cannot contact a patient or alter a care plan autonomously.
