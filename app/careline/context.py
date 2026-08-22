"""Clinician-authored recovery plan and transparent ambient demo signals."""

from copy import deepcopy

RECOVERY_PLAN = {
    "plan_id": "anchor-demo-plan-01",
    "author": "Dr. Maya Chen",
    "program": "Early recovery / outpatient",
    "today": [
        "Attend the 7:00 PM peer-support meeting",
        "Call sponsor Maya before bed",
        "Put the phone outside the bedroom at 10:30 PM",
    ],
    "check_in": ["craving intensity from 0-10", "sleep", "today's coping plan"],
    "options": [
        "Try four rounds of box breathing right now",
        "Urge surf for ten minutes and notice the urge rise and fall",
        "Move to a safer setting and call sponsor Maya",
        "Drink water and take a short walk before deciding the next step",
        "Join the 7:00 PM peer-support meeting early",
    ],
    "on_call": "Anchor Recovery on-call clinician",
}

_SIGNALS: dict[str, list[dict]] = {
    "self-jai": [
        {
            "type": "activity",
            "label": "Daily activity",
            "value": 3100,
            "baseline": 6200,
            "unit": "steps",
            "status": "below-baseline",
        },
        {
            "type": "check_in",
            "label": "Evening check-in",
            "value": "missed",
            "baseline": "completed",
            "unit": "",
            "status": "missed",
        },
    ]
}


def set_signal(resident_id: str, signal: dict) -> list[dict]:
    signals = _SIGNALS.setdefault(resident_id, [])
    signals[:] = [item for item in signals if item["type"] != signal["type"]]
    signals.append(signal)
    return deepcopy(signals)


def get_context(resident_id: str) -> dict:
    signals = deepcopy(_SIGNALS.get(resident_id, _SIGNALS["self-jai"]))
    reasons = [item["label"] for item in signals if item["status"] != "normal"]
    return {
        "plan": deepcopy(RECOVERY_PLAN),
        "signals": signals,
        "triggered": bool(reasons),
        "trigger_reason": " + ".join(reasons) if reasons else "Scheduled check-in",
        "synthetic_demo_data": True,
    }


def prompt_block(resident_id: str) -> str:
    context = get_context(resident_id)
    plan = context["plan"]
    return (
        f"CLINICIAN-AUTHORED PLAN ({plan['author']}):\n"
        + "Today's commitments:\n- "
        + "\n- ".join(plan["today"])
        + "\nAllowed in-the-moment options (offer 3-5 only when useful):\n- "
        + "\n- ".join(plan["options"])
        + f"\nAmbient trigger: {context['trigger_reason']} (synthetic demo signals)."
    )
