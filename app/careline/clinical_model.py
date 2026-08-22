"""Persisted clinical graph, reference library, and goal-target tracking."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from . import fixtures


def _load_references() -> tuple[str, list[dict]]:
    path = os.path.join(os.path.dirname(__file__), "bh-reference-library.seed.json")
    with open(path, encoding="utf-8") as source:
        payload = json.load(source)
    references = payload.get("references", [])
    if not references or len({item["reference_id"] for item in references}) != len(references):
        raise RuntimeError("reference library seed must contain unique entries")
    return payload["catalog_version"], references


REFERENCE_VERSION, REFERENCES = _load_references()

RISK_TIERS = [
    {"risk_tier_id": "tier-3", "label": "Immediate", "priority": 1, "response_minutes": 0, "safety_tier": 3, "action": "escalate_to_clinician"},
    {"risk_tier_id": "tier-2", "label": "Elevated", "priority": 2, "response_minutes": 30, "safety_tier": 2, "action": "flag_pattern_for_clinician"},
    {"risk_tier_id": "tier-1", "label": "Watch", "priority": 3, "response_minutes": 240, "safety_tier": 1, "action": "surface_reference"},
    {"risk_tier_id": "tier-0", "label": "Routine", "priority": 4, "response_minutes": 1440, "safety_tier": 0, "action": "scheduled_follow_up"},
]


def initialize(db: Database, timestamp: datetime, patients: list[dict], initial_plan: dict) -> None:
    patient_ids = [patient["patient_id"] for patient in patients]
    db.clinicians.create_index("clinician_id", unique=True)
    db.care_teams.create_index("care_team_id", unique=True)
    db.care_teams.create_index("patient_ids")
    db.conditions.create_index([("patient_id", ASCENDING), ("condition_id", ASCENDING)], unique=True)
    db.care_plan_revisions.create_index([("patient_id", ASCENDING), ("version", DESCENDING)], unique=True)
    db.goals.create_index("goal_id", unique=True)
    db.goals.create_index([("patient_id", ASCENDING), ("status", ASCENDING)])
    db.goal_observations.create_index("observation_id", unique=True)
    db.goal_observations.create_index([("patient_id", ASCENDING), ("goal_id", ASCENDING), ("observed_at", DESCENDING)])
    db.reference_library.create_index("reference_id", unique=True)
    db.reference_library.create_index([("category", ASCENDING), ("title", ASCENDING)])
    db.voice_risk_tiers.create_index("risk_tier_id", unique=True)
    db.voice_analyses.create_index("call_id", unique=True)
    db.voice_analyses.create_index([("patient_id", ASCENDING), ("created_at", DESCENDING)])
    db.clinical_notes.create_index("note_id", unique=True)
    db.clinical_notes.create_index([("patient_id", ASCENDING), ("authored_at", DESCENDING)])
    db.labs.create_index("lab_id", unique=True)
    db.labs.create_index([("patient_id", ASCENDING), ("collected_at", DESCENDING)])
    db.calls.create_index("call_id", unique=True)
    db.memories.create_index("memory_id", unique=True, sparse=True)
    db.alerts.create_index("fixture_id", unique=True, sparse=True)

    db.clinicians.update_one(
        {"clinician_id": "clinician-omar"},
        {"$setOnInsert": {"clinician_id": "clinician-omar", "display_name": "Omar Reed, LCSW", "role": "Recovery clinician", "synthetic_demo_data": True, "created_at": timestamp}, "$set": {"updated_at": timestamp}},
        upsert=True,
    )
    db.care_teams.update_one(
        {"care_team_id": "care-team-anchor-demo"},
        {"$setOnInsert": {"care_team_id": "care-team-anchor-demo", "name": "Anchor Recovery Team", "synthetic_demo_data": True, "created_at": timestamp}, "$set": {"clinician_ids": ["clinician-maya", "clinician-omar"], "patient_ids": patient_ids, "member_count": 2, "updated_at": timestamp}},
        upsert=True,
    )
    for index, patient in enumerate(patients):
        patient_id = patient["patient_id"]
        plan = fixtures.plan_for(patient, index)
        goal = fixtures.goal_for(patient, index)
        db.conditions.update_one(
            {"patient_id": patient_id, "condition_id": f"condition-{patient_id}-recovery"},
            {"$setOnInsert": {"condition_id": f"condition-{patient_id}-recovery", "patient_id": patient_id, "label": "Substance-use recovery support", "status": "active", "source": "Synthetic clinician chart", "recorded_at": timestamp - timedelta(days=30 + index), "synthetic_demo_data": True, "dataset_version": fixtures.DATASET_VERSION, "created_at": timestamp}},
            upsert=True,
        )
        db.care_plans.update_one(
            {"patient_id": patient_id},
            {"$setOnInsert": {**plan, "created_at": timestamp}, "$set": {"updated_at": timestamp}},
            upsert=True,
        )
        db.care_plan_revisions.update_one(
            {"patient_id": patient_id, "version": plan["version"]},
            {"$setOnInsert": {**plan, "published_at": timestamp, "published_by": plan["author"], "synthetic_demo_data": True}},
            upsert=True,
        )
        db.goals.update_one(
            {"goal_id": goal["goal_id"]},
            {"$setOnInsert": {**goal, "created_at": timestamp}, "$set": {"updated_at": timestamp}},
            upsert=True,
        )
        miss_count = 2 if patient["risk_tier_id"] == "tier-2" else 1 if patient["risk_tier_id"] == "tier-1" else 0
        for observation_index in range(2):
            status = "missed" if observation_index < miss_count else "met"
            observation_id = f"observation-{patient_id}-{observation_index + 1}"
            db.goal_observations.update_one(
                {"observation_id": observation_id},
                {"$setOnInsert": {"observation_id": observation_id, "patient_id": patient_id, "goal_id": goal["goal_id"], "status": status, "value": status, "source": "synthetic-fixture", "observed_at": timestamp - timedelta(days=observation_index + 1), "synthetic_demo_data": True, "dataset_version": fixtures.DATASET_VERSION}},
                upsert=True,
            )
        note_id = f"note-{patient_id}-review"
        db.clinical_notes.update_one(
            {"note_id": note_id},
            {"$setOnInsert": {"note_id": note_id, "patient_id": patient_id, "title": "Recovery plan review", "body": f"Reviewed current supports and the next {goal['tracking_window_days']}-day goal window.", "author": patient["clinician_name"], "source": "Canonical synthetic chart", "authored_at": timestamp - timedelta(days=(index % 6) + 1), "synthetic_demo_data": True, "dataset_version": fixtures.DATASET_VERSION}},
            upsert=True,
        )
        if index % 4 != 0:
            lab_id = f"lab-{patient_id}-panel"
            db.labs.update_one(
                {"lab_id": lab_id},
                {"$setOnInsert": {"lab_id": lab_id, "patient_id": patient_id, "name": "Synthetic wellness panel", "value": "Within reference range", "unit": "status", "reference_range": "Demonstration only", "source": "Synthetic connected lab", "collected_at": timestamp - timedelta(days=(index % 12) + 2), "synthetic_demo_data": True, "dataset_version": fixtures.DATASET_VERSION}},
                upsert=True,
            )
        call_id = f"fixture-call-{patient_id}"
        if index < 12:
            db.calls.update_one(
                {"call_id": call_id},
                {"$setOnInsert": {"call_id": call_id, "patient_id": patient_id, "started_at": timestamp - timedelta(hours=index + 2), "ended_at": timestamp - timedelta(hours=index + 2, minutes=-6), "status": "complete", "summary": "Synthetic check-in reviewed the current plan and support step.", "concern_score": 3 if patient["risk_tier_id"] in {"tier-2", "tier-3"} else 0, "transcript": [{"role": "assistant", "text": "How did today's plan go?"}, {"role": "user", "text": "Synthetic response recorded for workflow testing."}], "care_plan_id": plan["plan_id"], "care_plan_version": plan["version"], "synthetic_demo_data": True, "dataset_version": fixtures.DATASET_VERSION}},
                upsert=True,
            )
            db.memories.update_one(
                {"memory_id": f"memory-{patient_id}-support"},
                {"$setOnInsert": {"memory_id": f"memory-{patient_id}-support", "patient_id": patient_id, "call_id": call_id, "fact": "Named a planned support step during the prior synthetic check-in", "created_at": timestamp - timedelta(hours=index + 2), "synthetic_demo_data": True, "dataset_version": fixtures.DATASET_VERSION}},
                upsert=True,
            )
            db.voice_analyses.update_one(
                {"call_id": call_id},
                {"$setOnInsert": {"analysis_id": f"analysis-{call_id}", "call_id": call_id, "patient_id": patient_id, "care_team_id": fixtures.CARE_TEAM_ID, "care_plan_id": plan["plan_id"], "care_plan_version": plan["version"], "risk_tier_id": patient["risk_tier_id"], "concern_score": 3 if patient["risk_tier_id"] in {"tier-2", "tier-3"} else 0, "summary": "Synthetic voice analysis linked to the current plan.", "status": "pending-review" if patient["unreviewed"] else "complete", "rule_version": "anchor-triage-2026-08-22", "source_evidence": patient["risk_reason"], "created_at": timestamp - timedelta(hours=index + 2), "synthetic_demo_data": True, "dataset_version": fixtures.DATASET_VERSION}},
                upsert=True,
            )
        if patient["risk_tier_id"] in {"tier-2", "tier-3"}:
            delivery_states = ("delivered", "failed", "not-configured")
            alert_status = "resolved" if index == 19 else "open"
            alert = {
                "fixture_id": f"alert-{patient_id}-current",
                "patient_id": patient_id,
                "call_id": call_id,
                "reason": patient["risk_reason"],
                "severity": "critical" if patient["risk_tier_id"] == "tier-3" else "medium",
                "alert_type": "safety-escalation" if patient["risk_tier_id"] == "tier-3" else "goal-pattern",
                "triage_tier": 3 if patient["risk_tier_id"] == "tier-3" else 2,
                "risk_tier_id": patient["risk_tier_id"],
                "pattern_key": None if patient["risk_tier_id"] == "tier-3" else f"goal-misses:{goal['goal_id']}",
                "status": alert_status,
                "destination": "on-call clinician",
                "agent_delivery": {"status": delivery_states[index % len(delivery_states)]},
                "created_at": timestamp - timedelta(minutes=index * 13),
                "synthetic_demo_data": True,
                "dataset_version": fixtures.DATASET_VERSION,
            }
            if alert_status == "resolved":
                alert.update({"resolved_at": timestamp - timedelta(minutes=10), "resolved_by": patient["clinician_name"], "resolution_note": "Reviewed in synthetic fixture"})
            db.alerts.update_one(
                {"fixture_id": alert["fixture_id"]},
                {"$setOnInsert": alert},
                upsert=True,
            )
    for reference in REFERENCES:
        db.reference_library.update_one(
            {"reference_id": reference["reference_id"]},
            {"$setOnInsert": {**reference, "catalog_version": REFERENCE_VERSION, "status": "active", "reviewed_by": "Dr. Maya Chen", "reviewed_at": timestamp, "synthetic_demo_data": True}},
            upsert=True,
        )
    for tier in RISK_TIERS:
        db.voice_risk_tiers.update_one(
            {"risk_tier_id": tier["risk_tier_id"]},
            {"$set": {**tier, "updated_at": timestamp}, "$setOnInsert": {"synthetic_demo_data": True, "created_at": timestamp}},
            upsert=True,
        )


def list_references(db: Database, categories: list[str] | None = None) -> list[dict]:
    query = {"status": "active"}
    if categories:
        query["category"] = {"$in": categories}
    return list(db.reference_library.find(query).sort([("category", ASCENDING), ("title", ASCENDING)]))


def relevant_references(db: Database, text: str, include_crisis: bool = False, limit: int = 3) -> list[dict]:
    lowered = text.lower()
    categories = None if include_crisis else ["coping", "psychoeducation"]
    matches = []
    for reference in list_references(db, categories):
        score = sum(1 for keyword in reference.get("keywords", []) if keyword in lowered)
        if score:
            matches.append((score, reference))
    matches.sort(key=lambda item: (-item[0], item[1]["reference_id"]))
    return [item[1] for item in matches[:limit]]


def record_goal_observation(
    db: Database,
    patient_id: str,
    goal_id: str,
    status: str,
    value: Any,
    source: str,
    call_id: str | None = None,
) -> dict | None:
    goal = db.goals.find_one({"goal_id": goal_id, "patient_id": patient_id, "status": "active"})
    if not goal:
        return None
    observation = {
        "observation_id": uuid.uuid4().hex,
        "patient_id": patient_id,
        "goal_id": goal_id,
        "status": status,
        "value": value,
        "source": source,
        "call_id": call_id,
        "observed_at": datetime.now(timezone.utc),
        "synthetic_demo_data": True,
    }
    db.goal_observations.insert_one(observation)
    return observation


def repeated_goal_misses(db: Database, patient_id: str) -> list[dict]:
    patterns = []
    for goal in db.goals.find({"patient_id": patient_id, "status": "active"}):
        since = datetime.now(timezone.utc) - timedelta(days=int(goal.get("tracking_window_days", 7)))
        count = db.goal_observations.count_documents(
            {"patient_id": patient_id, "goal_id": goal["goal_id"], "status": "missed", "observed_at": {"$gte": since}}
        )
        if count >= int(goal.get("miss_threshold", 2)):
            patterns.append({"goal_id": goal["goal_id"], "title": goal["title"], "miss_count": count, "tracking_window_days": goal.get("tracking_window_days", 7)})
    return patterns


def save_plan_revision(db: Database, plan: dict, actor: str) -> None:
    db.care_plan_revisions.insert_one(
        {**plan, "published_at": datetime.now(timezone.utc), "published_by": actor, "synthetic_demo_data": True}
    )


def save_voice_analysis(db: Database, call: dict, summary: str, concern_score: int) -> None:
    score = max(0, min(10, int(concern_score)))
    safety_alert = db.alerts.find_one(
        {"call_id": call["call_id"], "alert_type": "safety-escalation"}
    )
    pattern_alert = db.alerts.find_one(
        {"call_id": call["call_id"], "alert_type": "goal-pattern"}
    )
    tier = "tier-3" if safety_alert else "tier-2" if pattern_alert else "tier-1"
    review = safety_alert or pattern_alert
    plan = db.care_plans.find_one({"patient_id": call["patient_id"]}, {"plan_id": 1, "version": 1}) or {}
    review_fields = {}
    if review and review.get("status") == "resolved":
        review_fields = {
            "status": "resolved",
            "resolved_by": review.get("resolved_by_clinician_id"),
            "resolution_note": review.get("resolution_note"),
            "resolved_at": review.get("resolved_at"),
        }
    db.voice_analyses.update_one(
        {"call_id": call["call_id"]},
        {"$setOnInsert": {"analysis_id": f"analysis-{call['call_id']}", "call_id": call["call_id"], "patient_id": call["patient_id"], "care_team_id": "care-team-anchor-demo", "care_plan_id": plan.get("plan_id"), "care_plan_version": plan.get("version"), "risk_tier_id": tier, "concern_score": score, "summary": summary, "status": "pending-review" if tier != "tier-1" else "complete", "created_at": datetime.now(timezone.utc), "synthetic_demo_data": True, **review_fields}},
        upsert=True,
    )


def resolve_voice_analysis(db: Database, call_id: str, clinician_id: str, note: str) -> None:
    db.voice_analyses.update_one(
        {"call_id": call_id},
        {"$set": {"status": "resolved", "resolved_by": clinician_id, "resolution_note": note, "resolved_at": datetime.now(timezone.utc)}},
    )


def patient_graph(db: Database, patient_id: str) -> dict:
    return {
        "care_team": db.care_teams.find_one({"patient_ids": patient_id}),
        "conditions": list(db.conditions.find({"patient_id": patient_id})),
        "goals": list(db.goals.find({"patient_id": patient_id}).sort("created_at", DESCENDING)),
        "goal_patterns": repeated_goal_misses(db, patient_id),
        "voice_analyses": list(db.voice_analyses.find({"patient_id": patient_id}).sort("created_at", DESCENDING).limit(8)),
        "notes": list(db.clinical_notes.find({"patient_id": patient_id}).sort("authored_at", DESCENDING).limit(20)),
        "labs": list(db.labs.find({"patient_id": patient_id}).sort("collected_at", DESCENDING).limit(20)),
        "plan_revisions": list(db.care_plan_revisions.find({"patient_id": patient_id}).sort("version", DESCENDING).limit(12)),
    }
