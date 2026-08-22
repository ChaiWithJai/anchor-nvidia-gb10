"""Optional delivery of persisted safety alerts to the local OpenClaw agent."""

import os

import httpx


WAKE_URL = os.environ.get("CARELINE_OPENCLAW_WAKE_URL", "").strip()
HOOK_TOKEN = os.environ.get("CARELINE_OPENCLAW_HOOK_TOKEN", "").strip()


def status() -> dict:
    return {
        "name": "OpenClaw in NVIDIA OpenShell",
        "configured": bool(WAKE_URL and HOOK_TOKEN),
        "transport": "local-hook" if WAKE_URL else "disabled",
    }


async def notify(alert: dict) -> dict:
    if not WAKE_URL or not HOOK_TOKEN:
        return {"status": "not-configured", "target": "OpenClaw"}

    text = (
        f"Anchor {alert['severity']} clinician escalation for patient "
        f"{alert['resident_id']}. Alert {alert['alert_id']}. "
        f"{alert['reason']}. Review the persisted clinic alert now; do not "
        "contact the patient or alter the care plan autonomously."
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                WAKE_URL,
                headers={"Authorization": f"Bearer {HOOK_TOKEN}"},
                json={"text": text, "mode": "now"},
            )
            response.raise_for_status()
        return {
            "status": "delivered",
            "target": "OpenClaw",
            "http_status": response.status_code,
        }
    except httpx.HTTPError as exc:
        return {
            "status": "failed",
            "target": "OpenClaw",
            "error": type(exc).__name__,
        }
