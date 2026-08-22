"""Local MongoDB system of record for the synthetic clinic workload."""

import os
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.database import Database
from pymongo.errors import PyMongoError

from . import clinical_model


MONGO_URI = os.environ.get(
    "CARELINE_MONGO_URI",
    "mongodb://anchor:anchor-gb10-local-only@mongodb:27017/anchor?authSource=admin",
)
MONGO_DB = os.environ.get("CARELINE_MONGO_DB", "anchor")
_CLIENT: MongoClient | None = None

DEMO_PLAN = {
    "plan_id": "anchor-demo-plan-01",
    "patient_id": "demo-jai",
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
    "version": 1,
}

DEMO_SIGNALS = [
    {"type": "activity", "label": "Daily activity", "value": 3100, "baseline": 6200, "unit": "steps", "status": "below-baseline"},
    {"type": "check_in", "label": "Evening check-in", "value": "missed", "baseline": "completed", "unit": "", "status": "missed"},
]

DEMO_PATIENTS = [
    {
        "patient_id": "demo-jai", "display_name": "Jai", "age_band": "30-39",
        "program": "Early recovery / outpatient", "clinician_id": "clinician-maya",
        "clinician_name": "Dr. Maya Chen", "status": "active", "risk_band": "watch",
        "next_check_in": "Today, 7:30 PM", "voice_enrollment": "consented",
        "consent_version": "demo-2026-08-22", "synthetic_demo_data": True,
        "visible_in_clinic": True,
    },
    {
        "patient_id": "demo-dorothy", "display_name": "Dorothy", "age_band": "80-89",
        "program": "Recovery wellness / remote", "clinician_id": "clinician-maya",
        "clinician_name": "Dr. Maya Chen", "status": "active", "risk_band": "stable",
        "next_check_in": "Tomorrow, 9:00 AM", "voice_enrollment": "not-enrolled",
        "synthetic_demo_data": True, "visible_in_clinic": True,
    },
    {
        "patient_id": "demo-marcus", "display_name": "Marcus", "age_band": "40-49",
        "program": "Early recovery / intensive outpatient", "clinician_id": "clinician-maya",
        "clinician_name": "Dr. Maya Chen", "status": "active", "risk_band": "elevated",
        "next_check_in": "Today, 8:15 PM", "voice_enrollment": "pending",
        "synthetic_demo_data": True, "visible_in_clinic": True,
    },
]


def now() -> datetime:
    return datetime.now(timezone.utc)


def _db() -> Database:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = MongoClient(
            MONGO_URI, serverSelectionTimeoutMS=3_000, connectTimeoutMS=3_000,
            appname="anchor-gb10",
        )
    return _CLIENT[MONGO_DB]


def _public(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, list):
        return [_public(item) for item in value]
    if isinstance(value, dict):
        return {("id" if key == "_id" else key): _public(item) for key, item in value.items()}
    return value


def initialize() -> None:
    db = _db()
    db.command("ping")
    db.patients.create_index("patient_id", unique=True)
    db.patients.create_index([("visible_in_clinic", ASCENDING), ("display_name", ASCENDING)])
    db.care_plans.create_index("patient_id", unique=True)
    db.calls.create_index("call_id", unique=True)
    db.calls.create_index([("patient_id", ASCENDING), ("started_at", DESCENDING)])
    db.memories.create_index([("patient_id", ASCENDING), ("created_at", DESCENDING)])
    db.alerts.create_index([("status", ASCENDING), ("created_at", DESCENDING)])
    db.alerts.create_index([("patient_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)])
    db.signals.create_index([("patient_id", ASCENDING), ("type", ASCENDING)], unique=True)
    db.audit_events.create_index([("created_at", DESCENDING)])
    db.audit_events.create_index("event_key", unique=True, sparse=True)

    timestamp = now()
    for patient in DEMO_PATIENTS:
        db.patients.update_one(
            {"patient_id": patient["patient_id"]},
            {"$setOnInsert": {**patient, "created_at": timestamp}, "$set": {"updated_at": timestamp}},
            upsert=True,
        )
    db.clinicians.update_one(
        {"clinician_id": "clinician-maya"},
        {"$setOnInsert": {"clinician_id": "clinician-maya", "display_name": "Dr. Maya Chen", "role": "Clinical supervisor", "synthetic_demo_data": True, "created_at": timestamp}, "$set": {"updated_at": timestamp}},
        upsert=True,
    )
    db.care_plans.update_one(
        {"patient_id": "demo-jai"},
        {"$setOnInsert": {**DEMO_PLAN, "created_at": timestamp}, "$set": {"updated_at": timestamp}},
        upsert=True,
    )
    clinical_model.initialize(
        db,
        timestamp,
        DEMO_PATIENTS,
        DEMO_PLAN,
    )
    for signal in DEMO_SIGNALS:
        db.signals.update_one(
            {"patient_id": "demo-jai", "type": signal["type"]},
            {"$setOnInsert": {**signal, "patient_id": "demo-jai", "created_at": timestamp}, "$set": {"updated_at": timestamp}},
            upsert=True,
        )
    db.audit_events.update_one(
        {"event_key": "seed:clinic-demo-v1"},
        {"$setOnInsert": {"event_key": "seed:clinic-demo-v1", "action": "clinic.demo_seeded", "actor": "system", "patient_id": None, "detail": "Synthetic clinic fixtures initialized", "created_at": timestamp, "synthetic_demo_data": True}},
        upsert=True,
    )


def health() -> dict:
    try:
        db = _db()
        db.command("ping")
        info = db.client.admin.command("buildInfo")
        return {"ready": True, "engine": "MongoDB", "version": info.get("version", "8.0"), "database": MONGO_DB, "collections": len(db.list_collection_names())}
    except PyMongoError as exc:
        return {"ready": False, "engine": "MongoDB", "error": type(exc).__name__}


def audit(action: str, actor: str, patient_id: str | None = None, detail: str = "") -> None:
    _db().audit_events.insert_one({"action": action, "actor": actor, "patient_id": patient_id, "detail": detail, "created_at": now(), "synthetic_demo_data": True})


def ensure_patient(patient_id: str, display_name: str = "Demo patient") -> None:
    _db().patients.update_one(
        {"patient_id": patient_id},
        {"$setOnInsert": {"patient_id": patient_id, "display_name": display_name, "program": "Automated verification", "clinician_id": "clinician-maya", "clinician_name": "Dr. Maya Chen", "status": "test", "risk_band": "unknown", "voice_enrollment": "consented", "synthetic_demo_data": True, "visible_in_clinic": False, "created_at": now()}, "$set": {"updated_at": now()}},
        upsert=True,
    )


def start_call(call_id: str, patient_id: str, display_name: str = "Demo patient") -> None:
    ensure_patient(patient_id, display_name)
    _db().calls.update_one(
        {"call_id": call_id},
        {"$setOnInsert": {"call_id": call_id, "patient_id": patient_id, "started_at": now(), "status": "in-progress", "synthetic_demo_data": True}},
        upsert=True,
    )
    audit("call.started", "anchor-agent", patient_id, call_id)


def end_call(call_id: str, summary: str, concern_score: int, transcript: list[dict] | None = None) -> None:
    call = _db().calls.find_one_and_update(
        {"call_id": call_id},
        {"$set": {"ended_at": now(), "status": "complete", "summary": summary, "concern_score": concern_score, "transcript": transcript or []}},
        return_document=ReturnDocument.AFTER,
    )
    if call:
        clinical_model.save_voice_analysis(_db(), call, summary, concern_score)
        _db().patients.update_one({"patient_id": call["patient_id"]}, {"$set": {"last_check_in_at": now(), "last_summary": summary, "updated_at": now()}})
        audit("call.completed", "anchor-agent", call["patient_id"], call_id)


def save_facts(patient_id: str, call_id: str, facts: list[str]) -> None:
    if facts:
        timestamp = now()
        _db().memories.insert_many([{"patient_id": patient_id, "fact": fact, "call_id": call_id, "created_at": timestamp, "synthetic_demo_data": True} for fact in facts])


def recall(patient_id: str, limit: int = 12) -> list[dict]:
    rows = _db().memories.find({"patient_id": patient_id}).sort("created_at", DESCENDING).limit(limit)
    return [_public(row) for row in rows]


def recent_calls(patient_id: str, limit: int = 5) -> list[dict]:
    rows = _db().calls.find({"patient_id": patient_id, "ended_at": {"$exists": True}}).sort("started_at", DESCENDING).limit(limit)
    return [_public(row) for row in rows]


def save_alert(
    patient_id: str,
    call_id: str,
    reason: str,
    severity: str,
    alert_type: str = "safety-escalation",
    tier: int = 3,
    pattern_key: str | None = None,
) -> str:
    if pattern_key:
        existing = _db().alerts.find_one(
            {"patient_id": patient_id, "pattern_key": pattern_key, "status": "open"}
        )
        if existing:
            return str(existing["_id"])
    result = _db().alerts.insert_one({"patient_id": patient_id, "call_id": call_id, "reason": reason, "severity": severity, "alert_type": alert_type, "triage_tier": tier, "pattern_key": pattern_key, "status": "open", "destination": "on-call clinician", "created_at": now(), "synthetic_demo_data": True})
    _db().patients.update_one({"patient_id": patient_id}, {"$set": {"risk_band": "elevated", "updated_at": now()}})
    audit("alert.created", "anchor-agent", patient_id, f"{severity}: {reason}")
    return str(result.inserted_id)

def set_alert_delivery(alert_id: str, delivery: dict) -> None:
    try:
        object_id = ObjectId(alert_id)
    except Exception:
        return
    _db().alerts.update_one(
        {"_id": object_id},
        {"$set": {"agent_delivery": delivery, "updated_at": now()}},
    )



def list_alerts(limit: int = 20, status: str | None = None) -> list[dict]:
    rows = _db().alerts.find({"status": status} if status else {}).sort("created_at", DESCENDING).limit(limit)
    return [_public(row) for row in rows]


def resolve_alert(
    alert_id: str,
    actor: str,
    note: str,
    clinician_id: str = "clinician-maya",
) -> dict | None:
    try:
        object_id = ObjectId(alert_id)
    except Exception:
        return None
    alert = _db().alerts.find_one_and_update(
        {"_id": object_id, "status": "open"},
        {"$set": {"status": "resolved", "resolved_at": now(), "resolved_by": actor, "resolved_by_clinician_id": clinician_id, "resolution_note": note}},
        return_document=ReturnDocument.AFTER,
    )
    if alert:
        clinical_model.resolve_voice_analysis(
            _db(), alert["call_id"], clinician_id, note
        )
        audit("alert.resolved", actor, alert["patient_id"], note)
    return _public(alert) if alert else None


def set_signal(patient_id: str, signal: dict) -> list[dict]:
    timestamp = now()
    _db().signals.update_one(
        {"patient_id": patient_id, "type": signal["type"]},
        {"$set": {**signal, "patient_id": patient_id, "updated_at": timestamp}, "$setOnInsert": {"created_at": timestamp}},
        upsert=True,
    )
    goal_id = signal.get("goal_id")
    if goal_id and signal.get("status") in {"met", "missed"}:
        clinical_model.record_goal_observation(
            _db(), patient_id, goal_id, signal["status"], signal.get("value"), "ambient-signal"
        )
    audit("signal.recorded", "ambient-agent", patient_id, signal["label"])
    return get_context(patient_id)["signals"]


def get_context(patient_id: str) -> dict:
    db = _db()
    plan = db.care_plans.find_one({"patient_id": patient_id}) or {**DEMO_PLAN, "patient_id": patient_id}
    signals = list(db.signals.find({"patient_id": patient_id}).sort("type", ASCENDING))
    if not signals:
        signals = [dict(item) for item in DEMO_SIGNALS]
    reasons = [item["label"] for item in signals if item.get("status") != "normal"]
    references = clinical_model.list_references(db, ["coping", "psychoeducation"])
    goals = list(db.goals.find({"patient_id": patient_id, "status": "active"}))
    goal_patterns = clinical_model.repeated_goal_misses(db, patient_id)
    return {"plan": _public(plan), "signals": _public(signals), "goals": _public(goals), "goal_patterns": _public(goal_patterns), "references": _public(references), "triggered": bool(reasons or goal_patterns), "trigger_reason": " + ".join(reasons) if reasons else "Repeated goal misses" if goal_patterns else "Scheduled check-in", "synthetic_demo_data": True}


def reference_library(categories: list[str] | None = None) -> list[dict]:
    return _public(clinical_model.list_references(_db(), categories))


def relevant_references(text: str, include_crisis: bool = False) -> list[dict]:
    return _public(clinical_model.relevant_references(_db(), text, include_crisis))


def goal_miss_patterns(patient_id: str) -> list[dict]:
    return _public(clinical_model.repeated_goal_misses(_db(), patient_id))


def record_goal_observation(
    patient_id: str, goal_id: str, status: str, value: Any, source: str
) -> dict | None:
    observation = clinical_model.record_goal_observation(
        _db(), patient_id, goal_id, status, value, source
    )
    if observation:
        audit("goal.observed", source, patient_id, f"{goal_id}: {status}")
    return _public(observation) if observation else None


def _patient_view(patient: dict) -> dict:
    patient_id = patient["patient_id"]
    result = _public(patient)
    result["plan"] = get_context(patient_id)["plan"]
    result["recent_calls"] = recent_calls(patient_id, limit=8)
    result["memories"] = recall(patient_id, limit=12)
    result["alerts"] = [row for row in list_alerts(limit=100) if row.get("patient_id") == patient_id][:8]
    result.update(_public(clinical_model.patient_graph(_db(), patient_id)))
    return result


def list_patients() -> list[dict]:
    rows = _db().patients.find({"visible_in_clinic": True}).sort("display_name", ASCENDING)
    return [_patient_view(row) for row in rows]


def get_patient(patient_id: str) -> dict | None:
    patient = _db().patients.find_one({"patient_id": patient_id, "visible_in_clinic": True})
    return _patient_view(patient) if patient else None


def update_patient(patient_id: str, updates: dict, actor: str) -> dict | None:
    allowed = {"display_name", "age_band", "program", "status", "risk_band", "next_check_in", "clinician_name"}
    payload = {key: value for key, value in updates.items() if key in allowed and value is not None}
    if not payload:
        return get_patient(patient_id)
    patient = _db().patients.find_one_and_update(
        {"patient_id": patient_id, "visible_in_clinic": True},
        {"$set": {**payload, "updated_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    if patient:
        audit("patient.updated", actor, patient_id, ", ".join(sorted(payload)))
    return _patient_view(patient) if patient else None


def update_plan(patient_id: str, plan: dict, actor: str) -> dict | None:
    db = _db()
    if not db.patients.find_one({"patient_id": patient_id, "visible_in_clinic": True}):
        return None
    current = db.care_plans.find_one({"patient_id": patient_id}) or DEMO_PLAN
    version = int(current.get("version", 0)) + 1
    payload = {**plan, "patient_id": patient_id, "plan_id": current.get("plan_id", f"plan-{patient_id}"), "version": version, "updated_at": now()}
    db.care_plans.update_one({"patient_id": patient_id}, {"$set": payload, "$setOnInsert": {"created_at": now()}}, upsert=True)
    clinical_model.save_plan_revision(db, payload, actor)
    audit("care_plan.updated", actor, patient_id, f"version {version}")
    return get_context(patient_id)["plan"]


def clinic_dashboard() -> dict:
    db = _db()
    patient_ids = [row["patient_id"] for row in db.patients.find({"visible_in_clinic": True}, {"patient_id": 1})]
    today = now().replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "active_patients": db.patients.count_documents({"visible_in_clinic": True, "status": "active"}),
        "check_ins_today": db.calls.count_documents({"patient_id": {"$in": patient_ids}, "started_at": {"$gte": today}}),
        "open_alerts": db.alerts.count_documents({"patient_id": {"$in": patient_ids}, "status": "open"}),
        "plans_under_clinician_control": db.care_plans.count_documents({"patient_id": {"$in": patient_ids}}),
        "database": health(), "synthetic_demo_data": True,
    }


def recent_activity(limit: int = 30) -> list[dict]:
    return [_public(row) for row in _db().audit_events.find().sort("created_at", DESCENDING).limit(limit)]
