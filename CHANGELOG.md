# Changelog

## Live GB10 operations and clinical graph

- Added the private `/goal` real-time view for masked browser connections,
  NVIDIA GPU telemetry, active inference, request volume, and latency.
- Implemented the clinic ERD with care teams, conditions, goals, goal
  observations, immutable plan revisions, voice analyses, and risk tiers.
- Added the clinician-reviewed reference library and executable Tier 1/Tier 2
  goal-tracking behavior.

## 2.0.0 - 2026-08-22

- Added a MongoDB 8 clinical system of record with indexes and synthetic fixtures.
- Added clinician roster, care-plan editing, calls, transcripts, alerts, and audit UI.
- Split the patient experience into a focused, iPhone-safe phone-call interface.
- Added plan publishing and alert-resolution APIs with persisted audit events.
- Expanded local and public verification through the full safety and voice path.
- Added an authenticated OpenClaw wake adapter with MongoDB delivery evidence.
- Made high-risk speech deterministic and forbade unproven notification claims.
- Corrected the MongoDB runbook and verifier environment variable.

## 1.0.0 - 2026-08-22

- Extracted the CareLine self-call flow from `hybrid-ai-blueprints`.
- Added a self-contained NVIDIA GB10 Compose runtime.
- Pinned local Nemotron 3 Nano NVFP4 and CUDA Sesame CSM-1B execution.
- Corrected first-call self prompting, Nemotron token bounds, and CSM BF16 inputs.
- Added consent enforcement, real voice readiness, persistent memory, and a full
  call-lifecycle workload.
- Rebuilt the browser experience around outbound call states and digital-twin
  memory.
