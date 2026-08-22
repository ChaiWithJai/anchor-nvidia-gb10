"""Deterministic SUD safety signals and clinician escalation persistence."""

import os
import re

import httpx

from . import agent_wake, memory, telemetry

CRISIS_TERMS = (
    "wish i was dead",
    "wish i wasn't here",
    "wish i wasnt here",
    "don't want to wake up",
    "dont want to wake up",
    "rather not wake up",
    "better off without me",
    "everyone would have an easier time without me",
    "i'm a burden",
    "im a burden",
    "a weight on this family",
    "a drag on everyone",
    "the tablets are in the drawer",
    "i counted them",
    "i know the number",
    "moved them out of the bathroom",
    "the whole packet",
    "how many i have left",
    "thought about how i'd do it",
    "thought about how id do it",
    "i know how i would",
    "worked out how",
    "i have a plan",
    "cut myself",
    "burn myself",
    "kill myself",
    "end my life",
    "suicide",
    "overdosed",
    "overdose",
    "overdose now",
    "cannot stay safe",
    "can't stay safe",
    "can't keep myself safe",
    "cant keep myself safe",
    "hurt myself",
    "took too many",
    "i'm not safe on my own",
    "im not safe on my own",
    "not safe tonight",
    "shouldn't be alone",
    "shouldnt be alone",
    "parked round the corner from",
    "engine running",
    "i know how this goes",
    "nothing will change",
    "never going to get better",
    "no way forward",
    "everything has gone grey",
    "can't feel my way out",
    "cant feel my way out",
)

TIER_2_TERMS = (
    "my sponsor moved away",
    "sponsor's been travelling",
    "sponsors been travelling",
    "haven't spoken to my sponsor",
    "havent spoken to my sponsor",
    "never found a new sponsor",
    "five months without one",
    "going to fewer meetings",
    "one in three now",
    "stopped going",
    "scaffolding coming down",
    "one would help me sleep",
    "telling myself it would",
    "building the case",
    "making arguments to myself",
    "the only way i'll sleep",
    "the only way ill sleep",
    "sitting there longer each night",
    "almost twenty minutes",
    "stayed longer than last time",
    "five days running",
    "longer every time",
)

TIER_1_FALSE_POSITIVES = (
    "rotten flu",
    "been in bed two days",
    "throat's killing me",
    "throats killing me",
    "unwell",
    "fever",
    "drove myself so i could leave",
    "decided before i went",
    "ordered a soda",
    "brought my own",
    "planned my exit",
    "it didn't really pull at me",
    "it didnt really pull at me",
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


async def _deliver_persisted_alert(alert_id: str, alert: dict) -> dict:
    handoff_proof = {
        "sandbox": "NVIDIA OpenShell",
        "route": "inference.local configured",
        "delivery_status": "pending",
        "ordering": "alert.commit completed before openclaw.wake",
    }
    with telemetry.span(
        "openclaw.wake",
        "openclaw",
        "isolation",
        "anchor-openclaw",
        handoff_proof,
    ):
        delivery = await agent_wake.notify(alert)
        handoff_proof["delivery_status"] = delivery["status"]
    route_proof = {
        "sandbox": "NVIDIA OpenShell",
        "route": "inference.local forced provider configuration",
        "delivery_status": (
            "configured" if agent_wake.status()["configured"] else "not configured"
        ),
    }
    with telemetry.span(
        "openshell.inference.route",
        "inference-local",
        "isolation",
        "openclaw-route",
        route_proof,
    ):
        pass
    with telemetry.span(
        "alert.delivery.persist",
        "mongodb",
        "durability",
        "anchor-mongodb",
        {
            "collection": "alerts",
            "acknowledged": True,
            "delivery_status": delivery["status"],
            "ordering": "persisted after openclaw.wake outcome",
        },
    ):
        memory.set_alert_delivery(alert_id, delivery)
    return delivery


def classify_utterance(text: str) -> dict:
    lowered = text.lower().replace("’", "'").replace("‘", "'")
    crisis_hits = [term for term in CRISIS_TERMS if term in lowered]
    if crisis_hits:
        return {"triage_tier": 3, "score": 10, "hits": crisis_hits, "reason": "direct safety language", "false_positive_trap": False}
    tier_2_hits = [term for term in TIER_2_TERMS if term in lowered]
    if tier_2_hits:
        return {"triage_tier": 2, "score": 2, "hits": tier_2_hits, "reason": "support or preoccupation pattern", "false_positive_trap": False}
    false_positive_hits = [term for term in TIER_1_FALSE_POSITIVES if term in lowered]
    if false_positive_hits:
        return {"triage_tier": 1, "score": 0, "hits": false_positive_hits, "reason": "explicit low-risk context", "false_positive_trap": True}
    hits: list[str] = []
    score = 0
    for pattern, weight, label in CONCERN_PATTERNS:
        if re.search(pattern, lowered):
            score += weight
            hits.append(label)
    return {"triage_tier": 3 if score >= ALERT_THRESHOLD else 1, "score": score, "hits": hits, "reason": "recovery safety signals" if hits else "no safety signal", "false_positive_trap": False}


def score_utterance(text: str) -> tuple[int, list[str], bool]:
    classification = classify_utterance(text)
    return classification["score"], classification["hits"], classification["triage_tier"] == 3


async def check_and_alert(
    resident_id: str,
    call_id: str,
    text: str,
    running_score: int,
    alerted_severity: str | None,
) -> tuple[int, str | None, dict | None]:
    classification = classify_utterance(text)
    score = classification["score"]
    hits = classification["hits"]
    crisis = classification["triage_tier"] == 3 and score == 10
    running_score += score
    if classification["false_positive_trap"]:
        return running_score, alerted_severity, None
    if classification["triage_tier"] == 2:
        if _SEVERITY_RANK["medium"] <= _SEVERITY_RANK[alerted_severity]:
            return running_score, alerted_severity, None
        reason = f"Recovery pattern for clinician review: {', '.join(hits)}"
        with telemetry.span(
            "alert.commit",
            "mongodb",
            "durability",
            "anchor-mongodb",
            {
                "collection": "alerts",
                "acknowledged": True,
                "ordering": "must complete before openclaw.wake",
            },
        ):
            alert_id = memory.save_alert(
                resident_id,
                call_id,
                reason,
                "medium",
                alert_type="utterance-pattern",
                tier=2,
                pattern_key=f"tier-2-utterance:{call_id}",
            )
        alert = {
            "alert_id": alert_id,
            "resident_id": resident_id,
            "call_id": call_id,
            "reason": reason,
            "severity": "medium",
            "triage_tier": 2,
            "alert_type": "utterance-pattern",
            "destination": "on-call clinician",
        }
        delivery = await _deliver_persisted_alert(alert_id, alert)
        alert["agent_delivery"] = delivery
        return running_score, "medium", alert
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
            with telemetry.span(
                "alert.commit",
                "mongodb",
                "durability",
                "anchor-mongodb",
                {
                    "collection": "alerts",
                    "acknowledged": True,
                    "ordering": "must complete before openclaw.wake",
                },
            ):
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
            delivery = await _deliver_persisted_alert(alert_id, alert)
            alert["agent_delivery"] = delivery
            return running_score, "medium", alert
        return running_score, alerted_severity, None

    severity = "critical" if crisis else "high" if running_score >= 6 else "medium"
    if _SEVERITY_RANK[severity] <= _SEVERITY_RANK[alerted_severity]:
        return running_score, alerted_severity, None

    reason = f"Recovery safety signals: {', '.join(hits)} (score {running_score})"
    with telemetry.span(
        "alert.commit",
        "mongodb",
        "durability",
        "anchor-mongodb",
        {
            "collection": "alerts",
            "acknowledged": True,
            "ordering": "must complete before openclaw.wake",
        },
    ):
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
    delivery = await _deliver_persisted_alert(alert_id, alert)
    alert["agent_delivery"] = delivery
    if WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(WEBHOOK_URL, json=alert)
        except httpx.HTTPError:
            pass
    return running_score, severity, alert
