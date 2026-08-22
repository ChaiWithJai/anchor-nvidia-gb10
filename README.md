# Anchor NVIDIA GB10

An NVIDIA-only hackathon proof of concept for an outbound "call yourself"
experience. A local Nemotron model holds a short, memory-aware conversation and
Sesame CSM-1B speaks every digital-twin turn in the enrolled, consented voice.

The first screen is the application, not a landing page: consent, ring, connect,
talk by microphone or text, hear the clone, hang up, and see durable memories on
the next call.

## NVIDIA stack

- Dell Pro Max with GB10 (ARM64, CUDA compute capability 12.1)
- `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` served locally by NVIDIA vLLM
- Sesame CSM-1B native Transformers inference on CUDA BF16
- SQLite call summaries and cross-call memory on a named Docker volume
- Browser SpeechRecognition for microphone input; no cloud inference

The POC simulates the outbound phone lifecycle in the browser. It deliberately
does not dial the public telephone network, so no carrier credentials or call
charges are required for judging.

## Run

The T7 hackathon bundle supplies the model shards, CUDA wheelhouse, and private
voice enrollment. Those artifacts are mounted read-only and are never copied
into this repository.

```bash
export HACKATHON_BUNDLE=/media/dell/T7/hackathon-2026-08-22
./scripts/run-nvidia
```

Open <http://127.0.0.1:8100/>. The launcher waits for both Nemotron and a real
CSM synthesis, then runs the complete call workload before reporting ready.

Repeat verification without rebuilding:

```bash
CARELINE_BASE_URL=http://127.0.0.1:8100 python3 scripts/verify-nvidia.py
```

## Share across segmented Wi-Fi

Use the temporary HTTPS profile only for a staffed hackathon demonstration:

```bash
export HACKATHON_BUNDLE=/media/dell/T7/hackathon-2026-08-22
export ANCHOR_DEMO_ACCESS_KEY='choose-a-private-team-code'
./scripts/share-nvidia
```

The launcher restarts only the application with signed-cookie access enabled,
starts a pinned Cloudflare quick-tunnel container, verifies that private APIs
reject anonymous requests, and prints the temporary `trycloudflare.com` URL.
Share the access code separately from the URL. Each browser receives a distinct
resident ID so attendee memories do not mix.

Nemotron, CSM, deterministic escalation, and SQLite remain on the GB10. Remote
HTTP traffic is transported through Cloudflare, so do not describe shared mode
as network-free or use it with real patient data. Quick tunnels are ephemeral,
best-effort demo infrastructure, not a clinical deployment boundary.

Stop public access immediately after judging:

```bash
docker compose -f compose.nvidia.yml --profile share stop share-proxy
```

## Provenance

Anchor extends the canonical CareLine blueprint in
[`ChaiWithJai/hybrid-ai-blueprints`](https://github.com/ChaiWithJai/hybrid-ai-blueprints),
branch `blueprint/careline-wellness-checkin` at commit `5f967406`, combined with
the GB10 additions pinned in the T7 snapshot dated 2026-08-22. This repository
narrows that work to one publishable NVIDIA runtime and includes subsequent
prompt, readiness, consent, CUDA dtype, UI, and workload corrections.

## Public-repo boundary

`.gitignore` excludes environment files, databases, recordings, checkpoints,
and model weights. Do not commit a voice reference or its transcript. Only use
a voice with the owner's informed consent and disclose that the caller is a
digital twin.
