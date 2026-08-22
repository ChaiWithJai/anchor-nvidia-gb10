#!/usr/bin/env python3
"""Convert the combined FHIR bundle into MongoDB collection documents."""

from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / "combined-patient-bundles.json"
OUTPUT_DIR = BASE_DIR / "mongodb"
COLLECTION_DIR = OUTPUT_DIR / "collections"
RISK_TIERS_SOURCE = OUTPUT_DIR / "voice-risk-tiers.seed.json"
HEALTH_HISTORIES_SOURCE = OUTPUT_DIR / "health-histories.seed.json"


def reference_id(reference: str | None, resource_type: str) -> str | None:
    if not reference:
        return None
    prefix = f"{resource_type}/"
    return reference[len(prefix):] if reference.startswith(prefix) else reference


def first_coding(value: dict | None) -> dict:
    codings = (value or {}).get("coding", [])
    return codings[0] if codings else {}


def extension_value(resource: dict, url: str, value_key: str) -> str | None:
    for extension in resource.get("extension", []):
        if extension.get("url") == url:
            return extension.get(value_key)
    return None


def identifier_value(resource: dict, system: str) -> str | None:
    for identifier in resource.get("identifier", []):
        if identifier.get("system") == system:
            return identifier.get("value")
    return None


def operational_team_id(resource: dict) -> str | None:
    value = identifier_value(resource, "urn:anchor:operational-care-team")
    if not value or not value.startswith("ACT-"):
        return None
    return f"careteam-{value.removeprefix('ACT-')}"


def build_collections(resources: list[dict]) -> dict[str, list[dict]]:
    groups = {
        resource["id"]: [
            reference_id(member.get("entity", {}).get("reference"), "Patient")
            for member in resource.get("member", [])
        ]
        for resource in resources
        if resource["resourceType"] == "Group"
    }
    group_resources = {
        resource["id"]: resource
        for resource in resources
        if resource["resourceType"] == "Group"
    }
    patient_care_teams = [
        resource for resource in resources if resource["resourceType"] == "CareTeam"
    ]
    care_team_by_patient = {
        reference_id(resource.get("subject", {}).get("reference"), "Patient"): resource
        for resource in patient_care_teams
    }

    collections: dict[str, list[dict]] = {
        "patients": [],
        "clinicians": [],
        "careTeams": [],
        "conditions": [],
        "goals": [],
        "carePlans": [],
        "voiceRiskTiers": [],
        "healthHistories": [],
    }

    for resource in resources:
        kind = resource["resourceType"]

        if kind == "Patient":
            collections["patients"].append(
                {
                    "_id": resource["id"],
                    "resourceType": kind,
                    "identifiers": resource.get("identifier", []),
                    "names": resource.get("name", []),
                    "gender": resource.get("gender"),
                    "birthDate": resource.get("birthDate"),
                    "telecom": resource.get("telecom", []),
                    "addresses": resource.get("address", []),
                    "maritalStatus": resource.get("maritalStatus", {}),
                    "communications": resource.get("communication", []),
                    "employmentStatus": extension_value(
                        resource, "urn:anchor:employment-status", "valueCode"
                    ),
                    "tags": resource.get("meta", {}).get("tag", []),
                }
            )

        elif kind == "Practitioner":
            name = (resource.get("name") or [{}])[0]
            collections["clinicians"].append(
                {
                    "_id": resource["id"],
                    "resourceType": kind,
                    "givenNames": name.get("given", []),
                    "familyName": name.get("family"),
                    "displayName": name.get("text"),
                    "identifiers": resource.get("identifier", []),
                    "telecom": resource.get("telecom", []),
                    "qualifications": resource.get("qualification", []),
                    "tags": resource.get("meta", {}).get("tag", []),
                }
            )

        elif kind == "Condition":
            clinical = first_coding(resource.get("clinicalStatus"))
            verification = first_coding(resource.get("verificationStatus"))
            diagnosis = first_coding(resource.get("code"))
            collections["conditions"].append(
                {
                    "_id": resource["id"],
                    "resourceType": kind,
                    "patientId": reference_id(resource.get("subject", {}).get("reference"), "Patient"),
                    "clinicalStatus": clinical,
                    "verificationStatus": verification,
                    "categories": resource.get("category", []),
                    "diagnosis": {**diagnosis, "text": resource.get("code", {}).get("text")},
                    "onsetDateTime": resource.get("onsetDateTime"),
                    "notes": [note.get("text") for note in resource.get("note", [])],
                }
            )

        elif kind == "Goal":
            collections["goals"].append(
                {
                    "_id": resource["id"],
                    "resourceType": kind,
                    "patientId": reference_id(resource.get("subject", {}).get("reference"), "Patient"),
                    "lifecycleStatus": resource.get("lifecycleStatus"),
                    "description": resource.get("description", {}).get("text"),
                    "targets": [
                        {
                            "measure": target.get("measure", {}).get("text"),
                            "dueDate": target.get("dueDate"),
                        }
                        for target in resource.get("target", [])
                    ],
                }
            )

        elif kind == "CarePlan":
            patient_care_team_id = reference_id(
                (resource.get("careTeam") or [{}])[0].get("reference"), "CareTeam"
            )
            patient_care_team = next(
                (team for team in patient_care_teams if team["id"] == patient_care_team_id),
                {},
            )
            collections["carePlans"].append(
                {
                    "_id": resource["id"],
                    "resourceType": kind,
                    "patientId": reference_id(resource.get("subject", {}).get("reference"), "Patient"),
                    "identifiers": resource.get("identifier", []),
                    "title": resource.get("title"),
                    "description": resource.get("description"),
                    "status": resource.get("status"),
                    "intent": resource.get("intent"),
                    "created": resource.get("created"),
                    "authorClinicianId": reference_id(
                        resource.get("author", {}).get("reference"), "Practitioner"
                    ),
                    "careTeamId": operational_team_id(patient_care_team),
                    "patientCareTeamId": patient_care_team_id,
                    "conditionIds": [
                        reference_id(condition.get("reference"), "Condition")
                        for condition in resource.get("addresses", [])
                    ],
                    "categories": resource.get("category", []),
                    "period": resource.get("period", {}),
                    "goalIds": [
                        reference_id(goal.get("reference"), "Goal")
                        for goal in resource.get("goal", [])
                    ],
                    "activities": [
                        {
                            "position": position,
                            "status": activity.get("detail", {}).get("status"),
                            "description": activity.get("detail", {}).get("description"),
                            "schedule": activity.get("detail", {}).get("scheduledString"),
                        }
                        for position, activity in enumerate(resource.get("activity", []), start=1)
                    ],
                    "notes": [note.get("text") for note in resource.get("note", [])],
                }
            )

    # MongoDB keeps the application-friendly five-team view. Each document is
    # a projection of one operational FHIR Group plus its two patient-scoped
    # FHIR CareTeam resources.
    for group_id, patient_ids in groups.items():
        group = group_resources[group_id]
        scoped_teams = [care_team_by_patient[patient_id] for patient_id in patient_ids]
        template = scoped_teams[0]
        participant = (template.get("participant") or [{}])[0]
        role = (participant.get("role") or [{}])[0]
        collections["careTeams"].append(
            {
                "_id": operational_team_id(group),
                "resourceType": "CareTeam",
                "sourceGroupId": group_id,
                "patientCareTeamIds": [team["id"] for team in scoped_teams],
                "name": group.get("name", "").removesuffix(" patient cohort"),
                "status": template.get("status"),
                "identifiers": group.get("identifier", []),
                "categories": template.get("category", []),
                "period": template.get("period", {}),
                "telecom": template.get("telecom", []),
                "patientIds": patient_ids,
                "clinicianId": reference_id(
                    participant.get("member", {}).get("reference"), "Practitioner"
                ),
                "clinicianRole": role.get("text"),
                "notes": [note.get("text") for note in template.get("note", [])],
            }
        )

    return collections


def validate(collections: dict[str, list[dict]]) -> None:
    expected = {
        "patients": 10,
        "clinicians": 2,
        "careTeams": 5,
        "conditions": 11,
        "goals": 10,
        "carePlans": 10,
        "voiceRiskTiers": 3,
        "healthHistories": 10,
    }
    for collection, expected_count in expected.items():
        actual = len(collections[collection])
        if actual != expected_count:
            raise ValueError(f"{collection}: expected {expected_count}, found {actual}")

    patient_ids = {patient["_id"] for patient in collections["patients"]}
    clinician_ids = {clinician["_id"] for clinician in collections["clinicians"]}
    care_team_ids = {team["_id"] for team in collections["careTeams"]}
    for patient in collections["patients"]:
        if not patient.get("telecom") or not patient.get("addresses"):
            raise ValueError(f"{patient['_id']} is missing realistic contact or address data")
        if not patient.get("employmentStatus") or not patient.get("maritalStatus"):
            raise ValueError(f"{patient['_id']} is missing enriched demographic data")
    assigned_patients = []
    for team in collections["careTeams"]:
        if len(team["patientIds"]) != 2 or len(set(team["patientIds"])) != 2:
            raise ValueError(f"{team['_id']} must have exactly two unique patients")
        if not set(team["patientIds"]).issubset(patient_ids):
            raise ValueError(f"{team['_id']} contains an unknown patient")
        if team["clinicianId"] not in clinician_ids:
            raise ValueError(f"{team['_id']} contains an unknown clinician")
        if len(team["patientCareTeamIds"]) != 2:
            raise ValueError(f"{team['_id']} must project exactly two patient CareTeams")
        assigned_patients.extend(team["patientIds"])
    if len(assigned_patients) != 10 or len(set(assigned_patients)) != 10:
        raise ValueError("each patient must belong to exactly one care team")

    goal_ids = {goal["_id"] for goal in collections["goals"]}
    condition_ids = {condition["_id"] for condition in collections["conditions"]}
    tier_ids = {tier["_id"] for tier in collections["voiceRiskTiers"]}
    for collection in ("conditions", "goals", "carePlans"):
        for document in collections[collection]:
            if document["patientId"] not in patient_ids:
                raise ValueError(f"{collection}/{document['_id']} contains an unknown patient")
    for care_plan in collections["carePlans"]:
        if not set(care_plan["goalIds"]).issubset(goal_ids):
            raise ValueError(f"carePlans/{care_plan['_id']} contains an unknown goal")
        if not set(care_plan["conditionIds"]).issubset(condition_ids):
            raise ValueError(f"carePlans/{care_plan['_id']} contains an unknown condition")
        if care_plan["careTeamId"] not in care_team_ids:
            raise ValueError(f"carePlans/{care_plan['_id']} contains an unknown care team")
        team = next(item for item in collections["careTeams"] if item["_id"] == care_plan["careTeamId"])
        if care_plan["patientCareTeamId"] not in team["patientCareTeamIds"]:
            raise ValueError(f"carePlans/{care_plan['_id']} contains an unknown patient CareTeam")
        if care_plan["authorClinicianId"] not in clinician_ids:
            raise ValueError(f"carePlans/{care_plan['_id']} contains an unknown author")

    history_patient_ids = [history["patientId"] for history in collections["healthHistories"]]
    if len(history_patient_ids) != len(set(history_patient_ids)) or set(history_patient_ids) != patient_ids:
        raise ValueError("each patient must have exactly one health-history document")
    for history in collections["healthHistories"]:
        if not history.get("synthetic"):
            raise ValueError(f"{history['_id']} must be explicitly marked synthetic")
        if not history.get("entries"):
            raise ValueError(f"{history['_id']} must contain history entries")
        for entry in history["entries"]:
            if not set(entry["relatedConditionIds"]).issubset(condition_ids):
                raise ValueError(f"{entry['historyEntryId']} references an unknown condition")
            if not set(entry["relatedGoalIds"]).issubset(goal_ids):
                raise ValueError(f"{entry['historyEntryId']} references an unknown goal")
            if entry["applicableTierId"] not in tier_ids:
                raise ValueError(f"{entry['historyEntryId']} references an unknown risk tier")
            if entry["applicableTierId"] == "tier-2-moderate":
                recurring = entry["consecutiveCheckIns"] >= 3
                repeated_goal_miss = entry["issueCode"] == "appointment_adherence_barrier" and entry["occurrenceCount"] > 1
                if not (recurring or repeated_goal_miss):
                    raise ValueError(f"{entry['historyEntryId']} does not meet the Tier 2 pattern rule")


def write_seed_script(collections: dict[str, list[dict]]) -> None:
    lines = [
        'const anchorDb = db.getSiblingDB("anchor_fhir");',
        "",
    ]
    for name, documents in collections.items():
        serialized = json.dumps(documents, indent=2, ensure_ascii=False)
        lines.extend(
            [
                f"const {name}Documents = {serialized};",
                f"for (const document of {name}Documents) {{",
                f'  anchorDb.getCollection("{name}").replaceOne(',
                "    { _id: document._id },",
                "    document,",
                "    { upsert: true }",
                "  );",
                "}",
                "",
            ]
        )
    (OUTPUT_DIR / "seed.mongodb.js").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))
    resources = [entry["resource"] for entry in bundle.get("entry", [])]
    collections = build_collections(resources)
    collections["voiceRiskTiers"] = json.loads(RISK_TIERS_SOURCE.read_text(encoding="utf-8"))
    collections["healthHistories"] = json.loads(HEALTH_HISTORIES_SOURCE.read_text(encoding="utf-8"))
    validate(collections)

    COLLECTION_DIR.mkdir(parents=True, exist_ok=True)
    for stale_file in COLLECTION_DIR.glob("*.json"):
        stale_file.unlink()
    for name, documents in collections.items():
        (COLLECTION_DIR / f"{name}.json").write_text(
            json.dumps(documents, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    write_seed_script(collections)


if __name__ == "__main__":
    main()
