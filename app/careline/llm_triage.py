"""Nemotron severity triage — the layer that generalises past the term lists.

`classify_utterance()` in escalation.py matches known phrasing. That is fast,
deterministic, and works when inference is down, but it only catches wording it
already encodes: on a 12-call blind holdout it reaches 67%, missing two callers
who describe wanting to die in words the lists do not contain --

    "the maths works out better for everyone if I'm not in it"
    "I've counted them twice this week and I don't like that I know the number"

This module reads the turn instead of matching it. Its rubric is grounded in
documented risk categories rather than any corpus, so it is not blind in the
same places the term lists are.

Two rules it must never break:

  1. It may only RAISE a tier. If a hallucination could lower one, a model
     error becomes a missed at-risk caller.
  2. A failure is an OPERATIONAL fault, not a clinical finding. Returning
     tier 3 on a timeout labels the patient's own words critical because our
     inference layer broke -- that produced seven over-alerts in twelve calls
     on the GB10 and is why this returns ok=False instead.
"""

from __future__ import annotations

import json
import logging
import os
import re

import httpx

log = logging.getLogger("careline.llm_triage")

ENABLED = os.environ.get("ANCHOR_LLM_TRIAGE", "1") not in ("0", "false", "no")
BASE_URL = os.environ.get("CARELINE_LLM_BASE_URL", "http://nemotron:8000/v1")
MODEL = os.environ.get("CARELINE_LLM_MODEL", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4")
TIMEOUT = float(os.environ.get("ANCHOR_LLM_TRIAGE_TIMEOUT", "20"))
MIN_CHARS = int(os.environ.get("ANCHOR_LLM_TRIAGE_MIN_CHARS", "40"))

RUBRIC = """You triage recovery check-in calls for a substance-use clinic. Assign exactly one severity tier.

TIER 3 - SEVERE / AT-RISK. Any one is sufficient:
- Suicidal ideation, active OR passive. Passive counts: wishing to be dead, wishing not to wake, believing others would be better off, describing oneself as a burden.
- Stating or implying they cannot keep themselves safe, are unsafe alone, or do not trust themselves.
- Means at hand: counting or moving medication, referencing a method.
- Self-harm, overdose, or a plan for either.
- Loss of control already happening, or use imminent.
- Refusing to engage, or hanging up rather than answering - a caller who supplies no information is NOT low risk.
- Hopelessness about the future, not merely a bad day.

TIER 2 - MODERATE. Deterioration without tier-3 features:
- A craving, trigger or risky behaviour that is recurring, escalating, or lasting longer.
- A coping strategy that stopped working or was abandoned.
- Support weakening: missed sessions, lost sponsor, growing isolation.
- Sleep collapse, or rationalising toward use.
- Asking for extra help because current arrangements are failing.

TIER 1 - MILD:
- Risk that was met and resolved. Mentioning a craving is NOT tier 2 if they describe managing it.
- Low mood, tiredness, grief or illness WITHOUT risk features.
- A routine or terse check-in.

RULES:
- Judge content, not tone. A calm voice describing means at hand is tier 3; an upset voice describing a resisted craving is tier 1.
- Never lower a tier because the caller minimises or apologises.
- When torn between two tiers, choose the HIGHER.

Reply with ONLY this JSON:
{"tier": 1|2|3, "category": "<short>", "rationale": "<one sentence quoting the deciding words>"}"""


def message_text(message: dict) -> str:
    """Pull assistant text out of a chat completion message.

    vLLM serving Nemotron with --reasoning-parser nemotron_v3 puts output in
    `reasoning_content` and may leave `content` null; some builds return
    `content` as a list of parts. Assuming a plain string silently turned every
    live call on the GB10 into a parse failure.
    """
    for key in ("content", "reasoning_content", "text"):
        val = message.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, list):
            joined = " ".join(
                part.get("text", "")
                for part in val
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )
            if joined.strip():
                return joined
    return ""


async def triage(text: str) -> tuple[int | None, str, bool]:
    """Returns (tier, rationale, ok). On any failure: (None, why, False)."""
    body = {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": 400,
        "messages": [
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content": text},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{BASE_URL}/chat/completions", json=body)
            response.raise_for_status()
            payload = response.json()
        message = (payload.get("choices") or [{}])[0].get("message") or {}
        raw = message_text(message)
        if not raw:
            log.warning("triage returned no text; message keys=%s", sorted(message))
            return None, "classifier returned no text", False
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            log.warning("triage returned no JSON: %r", raw[:300])
            return None, "classifier returned no JSON", False
        parsed = json.loads(match.group(0))
        if parsed.get("tier") not in (1, 2, 3):
            log.warning("triage returned no valid tier: %r", raw[:300])
            return None, "classifier returned no valid tier", False
        return int(parsed["tier"]), str(parsed.get("rationale", ""))[:300], True
    except Exception as exc:
        log.warning("triage failed: %s", exc)
        return None, f"classifier unreachable: {type(exc).__name__}", False


def should_run(text: str, current_tier: int) -> bool:
    """Skip when already tier 3, or the turn is too short to judge."""
    return ENABLED and current_tier < 3 and len(text.strip()) >= MIN_CHARS
