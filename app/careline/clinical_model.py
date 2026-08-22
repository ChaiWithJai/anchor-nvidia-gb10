"""Persisted clinical graph, reference library, and goal-target tracking."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database


REFERENCES = [
    {
        "reference_id": "ref-coping-box-breathing",
        "category": "coping",
        "title": "Box breathing",
        "spoken_copy": "Try four slow rounds: breathe in for four, hold for four, out for four, and hold for four.",
        "keywords": ["anxious", "panic", "overwhelmed", "sleep", "missed meeting"],
        "source": "clinician-reviewed demo reference",
    },
    {
        "reference_id": "ref-coping-urge-surfing",
        "category": "coping",
        "title": "Urge surfing",
        "spoken_copy": "Notice where the urge sits in your body and watch it rise and fall for ten minutes without acting on it.",
        "keywords": ["craving", "urge", "use", "relapse"],
        "source": "clinician-reviewed demo reference",
    },
    {
        "reference_id": "ref-psychoed-craving-curve",
        "category": "psychoeducation",
        "title": "Craving curve",
        "spoken_copy": "A craving can change in intensity over time; check the number again after a short coping step.",
        "keywords": ["craving", "urge", "strong", "intensity"],
        "source": "clinician-reviewed demo reference",
    },
    {
        "reference_id": "ref-crisis-988",
        "category": "crisis",
        "title": "988 Suicide & Crisis Lifeline",
        "spoken_copy": "In the United States, call or text 988 for immediate crisis support; call emergency services for immediate danger.",
        "keywords": ["suicide", "kill myself", "hurt myself", "cannot stay safe", "crisis"],
        "source": "https://988lifeline.org/get-help/",
    },
    {
        "reference_id": "ref-crisis-ndvh",
        "category": "crisis",
        "title": "National Domestic Violence Hotline",
        "spoken_copy": "If it is safe to do so, call 800-799-7233 or text START to 88788 to reach a live advocate.",
        "keywords": ["domestic violence", "partner hurt", "abuse", "unsafe at home"],
        "source": "https://www.thehotline.org/get-help/",
    },
]

RISK_TIERS = [
    {"risk_tier_id": "tier-1", "label": "In-conversation support", "min_score": 0, "max_score": 2, "action": "surface_reference"},
    {"risk_tier_id": "tier-2", "label": "Pattern review", "min_score": None, "max_score": None, "action": "flag_pattern_for_clinician"},
    {"risk_tier_id": "tier-3", "label": "Clinician escalation", "min_score": 3, "max_score": 10, "action": "escalate_to_clinician"},
]

DEMO_GOAL = {
    "goal_id": "goal-demo-jai-peer-support",
    "patient_id": "demo-jai",
    "title": "Attend the peer-support meeting",
    "target": 1,
    "unit": "completed meeting",
    "tracking_window_days": 7,
    "miss_threshold": 2,
    "status": "active",
    "reference_ids": ["ref-coping-urge-surfing", "ref-psychoed-craving-curve"],
}


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

    db.clinicians.update_one(
        {"clinician_id": "clinician-omar"},
        {"$setOnInsert": {"clinician_id": "clinician-omar", "display_name": "Omar Reed, LCSW", "role": "Recovery clinician", "synthetic_demo_data": True, "created_at": timestamp}, "$set": {"updated_at": timestamp}},
        upsert=True,
    )
    db.care_teams.update_one(
        {"care_team_id": "care-team-anchor-demo"},
        {"$setOnInsert": {"care_team_id": "care-team-anchor-demo", "name": "Anchor Recovery Team", "clinician_ids": ["clinician-maya", "clinician-omar"], "patient_ids": patient_ids, "member_count": 2, "synthetic_demo_data": True, "created_at": timestamp}, "$set": {"updated_at": timestamp}},
        upsert=True,
    )
    db.conditions.update_one(
        {"patient_id": "demo-jai", "condition_id": "condition-sud-recovery"},
        {"$setOnInsert": {"condition_id": "condition-sud-recovery", "patient_id": "demo-jai", "label": "Substance-use recovery support", "status": "active", "synthetic_demo_data": True, "created_at": timestamp}},
        upsert=True,
    )
    for patient in patients:
        patient_id = patient["patient_id"]
        plan = {
            **initial_plan,
            "plan_id": initial_plan["plan_id"] if patient_id == initial_plan["patient_id"] else f"plan-{patient_id}",
            "patient_id": patient_id,
            "program": patient["program"],
        }
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
        {"goal_id": DEMO_GOAL["goal_id"]},
        {"$setOnInsert": {**DEMO_GOAL, "created_at": timestamp, "synthetic_demo_data": True}, "$set": {"updated_at": timestamp}},
        upsert=True,
    )
    for reference in REFERENCES:
        db.reference_library.update_one(
            {"reference_id": reference["reference_id"]},
            {"$setOnInsert": {**reference, "status": "active", "reviewed_by": "Dr. Maya Chen", "reviewed_at": timestamp, "synthetic_demo_data": True}},
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
    }
