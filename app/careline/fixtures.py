"""Deterministic, synthetic outpatient-recovery demo population."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


DATASET_VERSION = "anchor-sud-roster-2026-08-22-v2"
CARE_TEAM_ID = "care-team-anchor-demo"

_PEOPLE = [
    ("demo-jai", "Jai", "30-39", "Early recovery / outpatient"),
    ("demo-dorothy", "Dorothy", "80-89", "Recovery wellness / remote"),
    ("demo-marcus", "Marcus", "40-49", "Early recovery / intensive outpatient"),
    ("demo-alina", "Alina", "20-29", "Early recovery / outpatient"),
    ("demo-ben", "Ben", "50-59", "Continuing care / outpatient"),
    ("demo-carmen", "Carmen", "30-39", "Early recovery / outpatient"),
    ("demo-devon", "Devon", "20-29", "Continuing care / remote"),
    ("demo-elena", "Elena", "40-49", "Early recovery / intensive outpatient"),
    ("demo-farid", "Farid", "50-59", "Continuing care / outpatient"),
    ("demo-grace", "Grace", "60-69", "Recovery wellness / remote"),
    ("demo-hana", "Hana", "30-39", "Early recovery / outpatient"),
    ("demo-isaac", "Isaac", "40-49", "Continuing care / outpatient"),
    ("demo-jordan", "Jordan", "20-29", "Early recovery / intensive outpatient"),
    ("demo-keisha", "Keisha", "30-39", "Early recovery / outpatient"),
    ("demo-luis", "Luis", "50-59", "Continuing care / remote"),
    ("demo-mei", "Mei", "40-49", "Recovery wellness / outpatient"),
    ("demo-nadia", "Nadia", "30-39", "Early recovery / outpatient"),
    ("demo-owen", "Owen", "60-69", "Continuing care / remote"),
    ("demo-priya", "Priya", "20-29", "Early recovery / intensive outpatient"),
    ("demo-quinn", "Quinn", "30-39", "Early recovery / outpatient"),
    ("demo-rafael", "Rafael", "40-49", "Continuing care / outpatient"),
    ("demo-samira", "Samira", "50-59", "Recovery wellness / remote"),
    ("demo-theo", "Theo", "20-29", "Early recovery / outpatient"),
    ("demo-uma", "Uma", "60-69", "Continuing care / outpatient"),
    ("demo-victor", "Victor", "40-49", "Early recovery / intensive outpatient"),
    ("demo-wren", "Wren", "30-39", "Early recovery / outpatient"),
    ("demo-xavier", "Xavier", "50-59", "Continuing care / remote"),
    ("demo-yasmin", "Yasmin", "20-29", "Early recovery / outpatient"),
    ("demo-zane", "Zane", "40-49", "Continuing care / outpatient"),
    ("demo-amara", "Amara", "30-39", "Recovery wellness / remote"),
]

_ELEVATED = {0, 5, 12, 19}
_WATCH = {3, 7, 10, 14, 18, 22, 26}
_IMMEDIATE = {2}
_VOICE_IDS = ("anchor-grounded", "anchor-warm", "anchor-clear", "anchor-gentle")


def dataset_anchor(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    return value.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def tier_for(index: int) -> tuple[str, int, str, str]:
    if index in _IMMEDIATE:
        return "tier-3", 1, "Immediate", "Review safety escalation now"
    if index in _ELEVATED:
        return "tier-2", 2, "Elevated", "Review repeated recovery-plan misses"
    if index in _WATCH:
        return "tier-1", 3, "Watch", "Review at next team huddle"
    return "tier-0", 4, "Routine", "Continue scheduled check-ins"


def build_patients(anchor: datetime) -> list[dict]:
    patients = []
    for index, (patient_id, name, age_band, program) in enumerate(_PEOPLE):
        tier_id, priority, label, next_action = tier_for(index)
        clinician_id = "clinician-maya" if index % 2 == 0 else "clinician-omar"
        clinician_name = "Dr. Maya Chen" if clinician_id == "clinician-maya" else "Omar Reed, LCSW"
        voice_mode = "personalized" if index in {0, 6, 16} else "text-only" if index % 9 == 0 else "catalog"
        patients.append(
            {
                "patient_id": patient_id,
                "display_name": name,
                "age_band": age_band,
                "program": program,
                "care_team_id": CARE_TEAM_ID,
                "clinician_id": clinician_id,
                "clinician_name": clinician_name,
                "status": "active",
                "risk_tier_id": tier_id,
                "risk_priority": priority,
                "risk_label": label,
                "risk_band": label.lower(),
                "risk_reason": (
                    "Direct safety language in the latest check-in"
                    if tier_id == "tier-3"
                    else "Two missed recovery-plan targets in seven days"
                    if tier_id == "tier-2"
                    else "Check-in or activity changed from baseline"
                    if tier_id == "tier-1"
                    else "No unresolved recovery-plan signal"
                ),
                "next_action": next_action,
                "action_due_at": anchor + timedelta(minutes=15 + index * 7),
                "tier_updated_at": anchor - timedelta(minutes=index * 13),
                "unreviewed": tier_id in {"tier-2", "tier-3"},
                "overdue": index in {2, 5, 12},
                "next_check_in": (anchor + timedelta(hours=(index % 8) + 1)).isoformat(),
                "last_check_in_at": anchor - timedelta(hours=(index % 10) + 2),
                "voice_mode": voice_mode,
                "voice_id": _VOICE_IDS[index % len(_VOICE_IDS)] if voice_mode == "catalog" else None,
                "voice_enrollment": "consented" if voice_mode == "personalized" else "not-required",
                "consent_version": "anchor-voice-2026-08-22" if voice_mode == "personalized" else None,
                "synthetic_demo_data": True,
                "dataset_version": DATASET_VERSION,
                "visible_in_clinic": True,
            }
        )
    return patients


def plan_for(patient: dict, index: int) -> dict:
    support = ("peer-support meeting", "sponsor check-in", "recovery group", "family support call")[index % 4]
    return {
        "plan_id": f"plan-{patient['patient_id']}",
        "patient_id": patient["patient_id"],
        "author": patient["clinician_name"],
        "program": patient["program"],
        "today": [f"Attend the scheduled {support}", "Complete the evening check-in", "Use the written coping plan before making a change"],
        "check_in": ["craving intensity from 0-10", "sleep", "today's coping plan"],
        "options": ["Try four rounds of box breathing right now", "Urge surf for ten minutes and notice the urge rise and fall", f"Contact the planned {support}", "Move to a safer setting", "Drink water and take a short walk"],
        "on_call": "Anchor Recovery on-call clinician",
        "version": 1,
        "synthetic_demo_data": True,
        "dataset_version": DATASET_VERSION,
    }


def goal_for(patient: dict, index: int) -> dict:
    titles = ("Attend the planned support meeting", "Complete the evening check-in", "Contact the named support person")
    return {
        "goal_id": f"goal-{patient['patient_id']}-weekly",
        "patient_id": patient["patient_id"],
        "title": titles[index % len(titles)],
        "target": 1,
        "unit": "completed action",
        "tracking_window_days": 7,
        "miss_threshold": 2,
        "status": "active",
        "reference_ids": ["ref-coping-urge-surfing", "ref-psychoed-craving-curve"],
        "synthetic_demo_data": True,
        "dataset_version": DATASET_VERSION,
    }


def validate_population(patients: list[dict]) -> None:
    ids = [patient["patient_id"] for patient in patients]
    if len(patients) != 30 or len(set(ids)) != 30:
        raise RuntimeError("synthetic roster must contain exactly 30 unique patients")
    if {patient["clinician_id"] for patient in patients} != {"clinician-maya", "clinician-omar"}:
        raise RuntimeError("synthetic roster must exercise both clinicians")
    required_tiers = {"tier-0", "tier-1", "tier-2", "tier-3"}
    if {patient["risk_tier_id"] for patient in patients} != required_tiers:
        raise RuntimeError("synthetic roster must exercise every queue tier")
