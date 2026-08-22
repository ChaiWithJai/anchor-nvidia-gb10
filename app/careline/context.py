"""Clinician-authored recovery plan and transparent ambient demo signals."""

from . import store



def set_signal(resident_id: str, signal: dict) -> list[dict]:
    return store.set_signal(resident_id, signal)


def get_context(resident_id: str) -> dict:
    return store.get_context(resident_id)


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
