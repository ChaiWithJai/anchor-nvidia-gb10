# Anchor NVIDIA GB10

An NVIDIA GB10 hackathon proof of concept for an outpatient recovery clinic.
Anchor gives clinicians a local care-operations console and gives patients an
outbound "call yourself" experience in an enrolled, consented voice.

The clinician authors the plan and reviews alerts, calls, transcripts, and an
audit trail. The patient consents, answers, speaks by microphone or text, hears
the clone, and hangs up. MongoDB carries the plan and call memory into the next
check-in.

## NVIDIA stack

- Dell Pro Max with GB10 (ARM64, CUDA compute capability 12.1)
- `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` served locally by NVIDIA vLLM
- Sesame CSM-1B native Transformers inference on CUDA BF16
- MongoDB 8 stores patients, plans, signals, calls, memories, alerts, and audit events
- OpenClaw 2026.7.1 and NVIDIA OpenShell 0.0.106 from the offline T7 bundle
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

Open the clinician console at <http://127.0.0.1:8100/> and the patient call at
<http://127.0.0.1:8100/patient>. The launcher waits for Nemotron, MongoDB, and a
real CSM synthesis, then runs the complete workload before reporting ready.

Repeat verification without rebuilding:

```bash
ANCHOR_DEMO_URL=http://127.0.0.1:8100 python3 scripts/verify-nvidia.py
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
Share the access code separately from the URL. Use synthetic records only.

Nemotron, CSM, deterministic escalation, and MongoDB remain on the GB10. Remote
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

## Safety boundary

Anchor is a wellness workflow demo, not medical care. The twin can only use the
clinician-authored plan and vetted self-directed options. Deterministic safety
scoring persists concerning turns for human review; crisis language tells the
patient to contact emergency or crisis services. It does not diagnose,
prescribe, or autonomously change a care plan.
