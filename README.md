# Anchor NVIDIA GB10

An NVIDIA GB10 hackathon proof of concept for an outpatient recovery clinic.
Anchor gives clinicians a local care-operations console and gives patients an
outbound "call yourself" experience in an enrolled, consented voice.

The clinician authors the plan and reviews alerts, calls, transcripts, and an
audit trail. The patient consents, answers, speaks by microphone or text, hears
the clone, and hangs up. MongoDB carries the plan and call memory into the next
check-in.

## Phase two: evaluation-driven development

Anchor is moving into phase two. The existing Nemotron workload is the
baseline for a paired comparison with **Ternary Bonsai 2 27B** and selected
Bonsai family models. The goal is to reduce the total memory footprint while
preserving measured application quality, then test how much additional local
clinical-operations work the GB10 can support alongside the ambient agent.

Equal quality, lower total cost, and useful spare capacity are hypotheses to
measure. A smaller checkpoint or a general benchmark score does not establish
the same result for Anchor. The first comparison keeps the application,
clinical rules, patient context, speech components, and workload fixed.

The program follows MLflow's
[evaluation-driven development workflow](https://mlflow.org/docs/latest/genai/datasets/end-to-end-workflow/).
Raw events and traces become reviewed annotations and versioned evaluation
datasets. Paired evaluations guide improvements, followed by release checks
and monitoring for differences between development and deployed behavior.
Supervised fine-tuning, distillation, pruning, and reinforcement learning are
separate possible experiments after measured failures justify them.

The [phase-two documentation](docs/README.md) contains the program:

- [Lineage](docs/phase-two-lineage.md) records the CareLine, Anchor, and model
  history, with exact identities and the limits of current evidence.
- [Evaluation plan](docs/phase-two-evaluation.md) defines data review,
  comparisons, improvement experiments, and release criteria.
- [Cost and capacity analysis](docs/phase-two-cost-analysis.md) defines local
  measurements and illustrative hosted bills, including the conditions for
  handling protected health information.

Implementation is tracked in [evaluation issue #21](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/21)
and [cost and capacity issue #22](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/22).

The MLflow setup includes an `Anchor Phase Two Evaluation` experiment and
empty candidate, development, holdout, and production-replay datasets.
Run `scripts/bootstrap-phase-two.py` in an MLflow environment to reproduce the
setup. The empty datasets are a starting structure, not completed annotations
or model-comparison results.

EHR integration is proposed work. An initial adapter would map approved events
into Anchor's existing records and return drafts for human review. Additional
local work could include summarizing logged activities or preparing follow-up
queues. Each workload must be evaluated alongside the live check-in workflow
before claiming that reduced model memory creates usable clinical capacity.

## NVIDIA stack

- Dell Pro Max with GB10 (ARM64, CUDA compute capability 12.1)
- `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` served locally by NVIDIA vLLM
- Sesame CSM-1B native Transformers inference on CUDA BF16
- MongoDB 8 stores patients, plans, signals, calls, memories, alerts, and audit events
- OpenClaw 2026.5.27 in NVIDIA OpenShell 0.0.106 from the offline T7 bundle
- Whisper tiny.en for microphone transcription on the GB10; no browser or cloud STT

The POC simulates the outbound phone lifecycle in the browser. It deliberately
does not dial the public telephone network, so no carrier credentials or call
charges are required for judging.

The clinician console opens on a server-sorted 30-patient action queue using
canonical Tier 3, Tier 2, Tier 1, and routine states. Search and filters preserve
the clinical priority order, and each patient panel exposes the chart, notes,
call history, labs, plan revisions, alerts, and audit history without leaving the
work surface. The patient surface behaves like a phone call: it requests the
microphone, detects an utterance boundary, sends a mono PCM WAV to the GB10,
transcribes it with local Whisper, and speaks the local model response. Raw
microphone audio is processed in memory and is not stored by Anchor.

Patients may choose one of four deterministic, reference-free CSM catalog voices,
a consented personalized enrollment, or text only. Catalog generation never uses
the private personalized reference audio.

Safety alerts are written to MongoDB before any agent handoff. When a local
OpenClaw hook is configured, Anchor wakes the OpenClaw agent inside NVIDIA
OpenShell and stores the HTTP delivery result on the same alert. When it is not
configured, the alert says `not-configured`; the patient UI does not claim that
a clinician was contacted. Spoken high-risk responses use deterministic,
clinician-authored options rather than improvised advice.

OpenClaw never contacts a patient or changes a care plan autonomously.

The canonical component, trust-boundary, data-flow, and failure-mode overview
is [SYSTEM-ARCHITECTURE.md](SYSTEM-ARCHITECTURE.md). It also defines the
`/goal` telemetry path and the Agent's Last Exam used to validate the design.

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

For text messaging through the existing app, see
[WebSocket messaging](docs/websocket-messaging.md). The same document explains
how to record deployment and verification commands in MLflow.

### Inspect local MongoDB

The optional `inspect` profile runs an authenticated mongo-express UI on the
GB10 loopback interface. It connects to the existing `mongodb` service over the
private Compose network; MongoDB port `27017` remains unpublished and the
existing `mongo-data` volume is unchanged.

```bash
export MONGO_EXPRESS_USERNAME=anchor-inspector
export MONGO_EXPRESS_PASSWORD='choose-a-separate-local-password'
docker compose -f compose.nvidia.yml --profile inspect up -d mongo-express
```

Open <http://127.0.0.1:8081/> and sign in with those two values. Override the
loopback port with `MONGO_EXPRESS_PORT` if `8081` is already in use. Keep this
developer tool on localhost and do not use it through the Cloudflare tunnel.
If no inspector credentials are exported, the local demo defaults are
`anchor-inspector` and `anchor-gb10-inspect-local-only`; set distinct values on
any shared workstation.

Stop the inspector without stopping Anchor or deleting its data:

```bash
docker compose -f compose.nvidia.yml --profile inspect stop mongo-express
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

Nemotron, CSM, Whisper, deterministic escalation, and MongoDB remain on the GB10. Remote
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
