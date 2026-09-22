# Verified GB10 deployment, September 22, 2026

Anchor is running with Nemotron 3 Nano NVFP4, Sesame CSM-1B, Whisper
tiny.en, and MongoDB. All three Compose services are healthy. The existing
full workload verifier and the live WebSocket verifier passed, including
voice generation, transcription, deterministic escalation, reconnection,
and persisted transcript readback. Nine transport tests passed locally and
inside the application image. A browser text-only check-in also completed.

The optional OpenClaw/OpenShell handoff is not configured. Alerts still
persist and report the handoff as not configured.

## Access from the configured workstation

- [Clinician console](http://127.0.0.1:8100/)
- [Patient check-in](http://127.0.0.1:8100/patient)
- [Deployment evidence in MLflow](http://127.0.0.1:5810/#/experiments/13)
- [Phase-two evaluation in MLflow](http://127.0.0.1:5810/#/experiments/14)

These addresses use the workstation's persistent SSH tunnel to the GB10.
They are local addresses, not public deployment URLs. The tunnel is managed
by the user LaunchAgent `com.prismml.anchor-gb10-tunnel`. The remote app
binds to loopback port 8100; MLflow binds to loopback port 5210.

The GB10 checkout is `~/anchor-nvidia-gb10`. Its private `.env` maps the
mounted T7 model bundle and sets the loopback bind address. Inspect or restart
the stack from that checkout with `docker compose -f compose.nvidia.yml ps`
or `docker compose -f compose.nvidia.yml up -d`. See the
[general runbook](../GB10-RUNBOOK.md) for verification commands.

## Evidence and limits

Deployment parent run: `0a1bfc3ae9ca4bc989f2e49b98b62a3f`.
Full workload run: `52ac3bab3d374ec4937267cdf6e11906`.
WebSocket run: `fce23d52566a4d34be525de34adbc0cf`.

The functional checks do not establish clinical quality. One synthetic
check-in summary attributed planned or suggested actions to the patient
as completed actions. [Issue #24](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/24)
tracks the failure. The real observed case is in the MLflow candidate
dataset with an unreviewed status; no expected label or passing quality
score was invented. Bonsai comparison and clinical review remain phase-two
work described in the [evaluation plan](phase-two-evaluation.md).

## Memory allocation and restoration

With the owner's approval, the user services `bonsai2-release.service` and
`official-qwen38-server.service` were stopped to make room for Anchor.
Keep them stopped while this full Anchor stack is using the machine.
To restore the prior inference endpoints, first stop Anchor's model and
application containers, then restart the prior services:

```bash
cd ~/anchor-nvidia-gb10
docker compose -f compose.nvidia.yml stop digital-twin nemotron
systemctl --user start bonsai2-release.service official-qwen38-server.service
```

This leaves MongoDB and its stored records intact. No model files or database
volumes need to be removed.
