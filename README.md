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
- OpenClaw 2026.5.27 in NVIDIA OpenShell 0.0.106 from the offline T7 bundle
- Browser SpeechRecognition for microphone input; no cloud inference

The POC simulates the outbound phone lifecycle in the browser. It deliberately
does not dial the public telephone network, so no carrier credentials or call
charges are required for judging.

Safety alerts are written to MongoDB before any agent handoff. When a local
OpenClaw hook is configured, Anchor wakes the OpenClaw agent inside NVIDIA
OpenShell and stores the HTTP delivery result on the same alert. When it is not
configured, the alert says `not-configured`; the patient UI does not claim that
a clinician was contacted. Spoken high-risk responses use deterministic,
clinician-authored options rather than improvised advice.

OpenClaw never contacts a patient or changes a care plan autonomously.

The base workload runs fail-closed without a hook. [OPENSHLL.md](OPENSHLL.md)
documents the validated optional OpenShell + OpenClaw handoff and its private
network boundary.

## Run

The T7 hackathon bundle supplies the model shards, CUDA wheelhouse, and private
voice enrollment. Those artifacts are mounted read-only and are never copied
into this repository.

```bash
export HACKATHON_BUNDLE=/media/dell/T7/hackathon-2026-08-22
./scripts/run-nvidia
```

Open the clinician console at <http://127.0.0.1:8100/>, the patient call at
<http://127.0.0.1:8100/patient>, and the live GB10 operations view at
<http://127.0.0.1:8100/goal>. The launcher waits for Nemotron, MongoDB, and a
real CSM synthesis, then runs the complete workload before reporting ready.

`/goal` samples `nvidia-smi` once per second and combines GPU utilization,
temperature, power, clocks, active Nemotron/CSM work, masked browser clients,
request counts, and latency in one private server-sent-event stream. Multiple
viewers share the cached GPU sample rather than spawning one profiler per page.

For concurrent worktrees, build a uniquely tagged application image and set
`ANCHOR_APP_IMAGE` when recreating only `digital-twin` with `--no-deps`.
Keep the canonical Compose project, Nemotron, MongoDB volume, GPU, and published
ports shared; do not start a second inference stack from another worktree.

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

The persisted clinical entities, relationships, indexes, and invariants are
documented in [DATA-MODEL.md](DATA-MODEL.md).

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
