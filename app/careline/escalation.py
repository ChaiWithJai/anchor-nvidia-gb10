"""Deterministic SUD safety signals and clinician escalation persistence."""

import os
import re

import httpx

from . import agent_wake, memory

CRISIS_TERMS = (
    "kill myself",
    "end my life",
    "suicide",
    "overdosed",
    "overdose now",
    "cannot stay safe",
    "can't stay safe",
    "hurt myself",
)

CONCERN_PATTERNS: tuple[tuple[str, int, str], ...] = (
    (r"\b(?:want|going|about) to use\b", 4, "intent to use"),
    (r"\b(?:might|could) use (?:tonight|today|again)\b", 3, "risk of use"),
    (r"\b(?:used|relapsed|slipped) (?:today|tonight|again)\b", 4, "reported use"),
    (r"\bcravings? (?:are|is|at|hit|jumped to) (?:[7-9]|10)\b", 3, "high craving"),
    (r"\bstrong (?:urge|craving)s?\b", 3, "high craving"),
    (r"\bmissed (?:my |the )?(?:meeting|appointment|visit)\b", 2, "missed support"),
    (r"\b(?:no sleep|didn't sleep|haven't slept)\b", 2, "sleep disruption"),
    (r"\b(?:isolating|cut off from everyone)\b", 2, "isolation"),
)

ALERT_THRESHOLD = int(os.environ.get("CARELINE_ALERT_THRESHOLD", "3"))
WEBHOOK_URL = os.environ.get("CARELINE_ALERT_WEBHOOK", "")
_SEVERITY_RANK = {None: 0, "medium": 1, "high": 2, "critical": 3}


def score_utterance(text: str) -> tuple[int, list[str], bool]:
    lowered = text.lower()
    crisis_hits = [term for term in CRISIS_TERMS if term in lowered]
    if crisis_hits:
        return 10, crisis_hits, True
    hits: list[str] = []
    score = 0
    for pattern, weight, label in CONCERN_PATTERNS:
        if re.search(pattern, lowered):
            score += weight
            hits.append(label)
    return score, hits, False


async def check_and_alert(
    resident_id: str,
    call_id: str,
    text: str,
    running_score: int,
    alerted_severity: str | None,
) -> tuple[int, str | None, dict | None]:
    score, hits, crisis = score_utterance(text)
    running_score += score
    if score == 0 or (running_score < ALERT_THRESHOLD and not crisis):
        patterns = memory.goal_miss_patterns(resident_id)
        open_pattern_keys = {
            item.get("pattern_key")
            for item in memory.list_alerts(limit=100, status="open")
            if item.get("patient_id") == resident_id
        }
        pattern = next(
            (
                item
                for item in patterns
                if f"goal-misses:{item['goal_id']}" not in open_pattern_keys
            ),
            None,
        )
        if pattern:
            pattern_key = f"goal-misses:{pattern['goal_id']}"
            reason = (
                f"Recovery Plan pattern: {pattern['title']} missed "
                f"{pattern['miss_count']} times in {pattern['tracking_window_days']} days"
            )
            alert_id = memory.save_alert(
                resident_id,
                call_id,
                reason,
                "medium",
                alert_type="goal-pattern",
                tier=2,
                pattern_key=pattern_key,
            )
            alert = {
                "alert_id": alert_id,
                "resident_id": resident_id,
                "call_id": call_id,
                "reason": reason,
                "severity": "medium",
                "triage_tier": 2,
                "alert_type": "goal-pattern",
                "destination": "on-call clinician",
            }
            delivery = await agent_wake.notify(alert)
            memory.set_alert_delivery(alert_id, delivery)
            alert["agent_delivery"] = delivery
            return running_score, "medium", alert
        return running_score, alerted_severity, None

    severity = "critical" if crisis else "high" if running_score >= 6 else "medium"
    if _SEVERITY_RANK[severity] <= _SEVERITY_RANK[alerted_severity]:
        return running_score, alerted_severity, None

    reason = f"Recovery safety signals: {', '.join(hits)} (score {running_score})"
    alert_id = memory.save_alert(resident_id, call_id, reason, severity)
    alert = {
        "alert_id": alert_id,
        "resident_id": resident_id,
        "call_id": call_id,
        "reason": reason,
        "severity": severity,
        "triage_tier": 3,
        "alert_type": "safety-escalation",
        "destination": "on-call clinician",
    }
    delivery = await agent_wake.notify(alert)
    memory.set_alert_delivery(alert_id, delivery)
    alert["agent_delivery"] = delivery
    if WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(WEBHOOK_URL, json=alert)
        except httpx.HTTPError:
            pass
    return running_score, severity, alert
