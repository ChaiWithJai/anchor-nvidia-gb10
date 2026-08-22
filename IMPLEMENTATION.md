# Implementation

## Call path

1. A clinician publishes a bounded recovery plan in the care console.
2. The patient confirms enrolled-voice consent and starts a browser call.
3. FastAPI loads the patient, plan, observed signals, and prior facts from
   MongoDB, then creates a call session.
4. Local NVIDIA vLLM generates one or two short spoken sentences with Nemotron
   3 Nano NVFP4. Thinking is disabled for live latency.
5. CUDA CSM conditions on the read-only 24 kHz reference and exact transcript,
   then returns a cloned WAV.
6. The browser accepts speech through SpeechRecognition or typed input.
7. Deterministic scoring persists concerning turns as clinician alerts, then
   produces exact plan-grounded escalation wording.
8. If configured, the local OpenClaw `/hooks/wake` endpoint receives an
   authenticated review task; its delivery result is stored on the MongoDB alert.
9. Hangup asks Nemotron for strict JSON facts plus a one-line summary and saves
   the call, transcript, facts, and audit evidence to MongoDB.

## Interfaces

- `/` is the clinician console: roster, risk state, care-plan editor, calls,
  transcripts, alerts, resolution controls, and audit activity.
- `/patient` is the focused phone surface: consent, ring, answer, voice/text
  turns, cloned playback, escalation disclosure, and hangup.
- `/goal` is the live GB10 control room: masked browser connections, one-second
  NVIDIA telemetry, active Nemotron and CSM work, request counts, and latency.

## Persisted clinical graph

MongoDB stores two-clinician care teams, conditions, goals and timestamped goal
observations, an active care plan plus immutable revisions, calls, voice
analyses, risk tiers, memories, alerts, and audit events. The clinician-reviewed
reference library is ID-addressable. Relevant Tier 1 entries can be surfaced in
conversation, while repeated misses inside a goal's tracking window create one
deduplicated Tier 2 pattern alert. See `DATA-MODEL.md` for the ERD.

## Runtime boundaries

`compose.nvidia.yml` is the deployment definition. The inference containers
reserve the NVIDIA GPU. Models and biometric enrollment stay outside Git and
mount read-only; only MongoDB writes to its named data volume. MongoDB has no
host port. The application runs
with a read-only root filesystem, dropped capabilities, and no-new-privileges.

CSM requests are serialized through one dedicated worker. Floating processor
inputs are converted to the loaded model dtype before generation, which avoids
the BF16/FP32 mismatch observed on GB10.

## Verification gates

`scripts/verify-nvidia.py` checks MongoDB health and both interfaces, publishes
a care plan, rejects a missing-consent call, opens a fresh self call, generates
a real cloned greeting WAV, checks low- and high-risk turns, verifies exact
escalation wording, agent-delivery audit state, and cloned reply audio, persists
the transcript, and opens a second call using stored memory.
