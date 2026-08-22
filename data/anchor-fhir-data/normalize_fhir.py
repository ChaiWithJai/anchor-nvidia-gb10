#!/usr/bin/env python3
"""Normalize the combined demo FHIR Bundle into SQLite and CSV tables."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / "combined-patient-bundles.json"
OUTPUT_DIR = BASE_DIR / "normalized"
CSV_DIR = OUTPUT_DIR / "tables"
DATABASE = OUTPUT_DIR / "normalized-fhir.sqlite"
SCHEMA_FILE = OUTPUT_DIR / "schema.sql"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY,
    gender TEXT,
    birth_date TEXT
);

CREATE TABLE patient_identifiers (
    identifier_id INTEGER PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    system TEXT,
    value TEXT NOT NULL,
    UNIQUE (system, value)
);

CREATE TABLE patient_names (
    name_id INTEGER PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    name_use TEXT,
    family TEXT
);

CREATE TABLE patient_name_given (
    name_id INTEGER NOT NULL REFERENCES patient_names(name_id),
    position INTEGER NOT NULL,
    given_name TEXT NOT NULL,
    PRIMARY KEY (name_id, position)
);

CREATE TABLE patient_addresses (
    address_id INTEGER PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    city TEXT,
    state TEXT,
    country TEXT
);

CREATE TABLE patient_tags (
    tag_id INTEGER PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    system TEXT,
    code TEXT
);

CREATE TABLE conditions (
    condition_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    clinical_system TEXT,
    clinical_code TEXT,
    verification_system TEXT,
    verification_code TEXT,
    diagnosis_system TEXT,
    diagnosis_code TEXT,
    diagnosis_display TEXT,
    diagnosis_text TEXT,
    onset_datetime TEXT
);

CREATE TABLE condition_categories (
    category_id INTEGER PRIMARY KEY,
    condition_id TEXT NOT NULL REFERENCES conditions(condition_id),
    system TEXT,
    code TEXT,
    display TEXT
);

CREATE TABLE condition_notes (
    note_id INTEGER PRIMARY KEY,
    condition_id TEXT NOT NULL REFERENCES conditions(condition_id),
    note_text TEXT NOT NULL
);

CREATE TABLE goals (
    goal_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    lifecycle_status TEXT,
    description TEXT
);

CREATE TABLE goal_targets (
    target_id INTEGER PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(goal_id),
    measure TEXT,
    due_date TEXT
);

CREATE TABLE care_plans (
    care_plan_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id),
    status TEXT,
    intent TEXT,
    period_start TEXT,
    period_end TEXT
);

CREATE TABLE care_plan_categories (
    category_id INTEGER PRIMARY KEY,
    care_plan_id TEXT NOT NULL REFERENCES care_plans(care_plan_id),
    system TEXT,
    code TEXT,
    display TEXT,
    category_text TEXT
);

CREATE TABLE care_plan_goals (
    care_plan_id TEXT NOT NULL REFERENCES care_plans(care_plan_id),
    goal_id TEXT NOT NULL REFERENCES goals(goal_id),
    PRIMARY KEY (care_plan_id, goal_id)
);

CREATE TABLE care_plan_activities (
    activity_id INTEGER PRIMARY KEY,
    care_plan_id TEXT NOT NULL REFERENCES care_plans(care_plan_id),
    position INTEGER NOT NULL,
    description TEXT,
    UNIQUE (care_plan_id, position)
);

CREATE TABLE clinicians (
    clinician_id TEXT PRIMARY KEY,
    given_name TEXT,
    family_name TEXT,
    display_name TEXT
);

CREATE TABLE care_teams (
    care_team_id TEXT PRIMARY KEY,
    status TEXT
);

CREATE TABLE care_team_patients (
    care_team_id TEXT NOT NULL REFERENCES care_teams(care_team_id),
    patient_id TEXT NOT NULL UNIQUE REFERENCES patients(patient_id),
    PRIMARY KEY (care_team_id, patient_id)
);

CREATE TABLE care_team_clinicians (
    care_team_id TEXT NOT NULL REFERENCES care_teams(care_team_id),
    clinician_id TEXT NOT NULL REFERENCES clinicians(clinician_id),
    role_text TEXT,
    PRIMARY KEY (care_team_id)
);

CREATE TABLE care_team_notes (
    note_id INTEGER PRIMARY KEY,
    care_team_id TEXT NOT NULL REFERENCES care_teams(care_team_id),
    note_text TEXT NOT NULL
);

CREATE INDEX idx_conditions_patient ON conditions(patient_id);
CREATE INDEX idx_goals_patient ON goals(patient_id);
CREATE INDEX idx_care_plans_patient ON care_plans(patient_id);
CREATE INDEX idx_care_team_patients_team ON care_team_patients(care_team_id);
CREATE INDEX idx_care_team_clinicians_clinician ON care_team_clinicians(clinician_id);
""".strip() + "\n"


def referenced_id(reference: str | None, expected_type: str) -> str | None:
    if not reference:
        return None
    prefix = f"{expected_type}/"
    return reference[len(prefix):] if reference.startswith(prefix) else reference


def first_coding(value: dict | None) -> dict:
    codings = (value or {}).get("coding", [])
    return codings[0] if codings else {}


def insert_resources(connection: sqlite3.Connection, resources: list[dict]) -> None:
    patients = [resource for resource in resources if resource["resourceType"] == "Patient"]
    for patient in patients:
        patient_id = patient["id"]
        connection.execute(
            "INSERT INTO patients VALUES (?, ?, ?)",
            (patient_id, patient.get("gender"), patient.get("birthDate")),
        )
        for identifier in patient.get("identifier", []):
            connection.execute(
                "INSERT INTO patient_identifiers(patient_id, system, value) VALUES (?, ?, ?)",
                (patient_id, identifier.get("system"), identifier.get("value")),
            )
        for name in patient.get("name", []):
            cursor = connection.execute(
                "INSERT INTO patient_names(patient_id, name_use, family) VALUES (?, ?, ?)",
                (patient_id, name.get("use"), name.get("family")),
            )
            for position, given_name in enumerate(name.get("given", []), start=1):
                connection.execute(
                    "INSERT INTO patient_name_given VALUES (?, ?, ?)",
                    (cursor.lastrowid, position, given_name),
                )
        for address in patient.get("address", []):
            connection.execute(
                "INSERT INTO patient_addresses(patient_id, city, state, country) VALUES (?, ?, ?, ?)",
                (patient_id, address.get("city"), address.get("state"), address.get("country")),
            )
        for tag in patient.get("meta", {}).get("tag", []):
            connection.execute(
                "INSERT INTO patient_tags(patient_id, system, code) VALUES (?, ?, ?)",
                (patient_id, tag.get("system"), tag.get("code")),
            )

    practitioners = [resource for resource in resources if resource["resourceType"] == "Practitioner"]
    for practitioner in practitioners:
        name = (practitioner.get("name") or [{}])[0]
        connection.execute(
            "INSERT INTO clinicians VALUES (?, ?, ?, ?)",
            (
                practitioner["id"],
                " ".join(name.get("given", [])) or None,
                name.get("family"),
                name.get("text"),
            ),
        )

    patient_groups = {
        resource["id"]: resource
        for resource in resources
        if resource["resourceType"] == "Group"
    }

    for resource in resources:
        kind = resource["resourceType"]
        patient_id = referenced_id(resource.get("subject", {}).get("reference"), "Patient")

        if kind == "Condition":
            clinical = first_coding(resource.get("clinicalStatus"))
            verification = first_coding(resource.get("verificationStatus"))
            diagnosis = first_coding(resource.get("code"))
            connection.execute(
                "INSERT INTO conditions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    resource["id"], patient_id,
                    clinical.get("system"), clinical.get("code"),
                    verification.get("system"), verification.get("code"),
                    diagnosis.get("system"), diagnosis.get("code"), diagnosis.get("display"),
                    resource.get("code", {}).get("text"), resource.get("onsetDateTime"),
                ),
            )
            for category in resource.get("category", []):
                for coding in category.get("coding", []) or [{}]:
                    connection.execute(
                        "INSERT INTO condition_categories(condition_id, system, code, display) VALUES (?, ?, ?, ?)",
                        (resource["id"], coding.get("system"), coding.get("code"), coding.get("display")),
                    )
            for note in resource.get("note", []):
                connection.execute(
                    "INSERT INTO condition_notes(condition_id, note_text) VALUES (?, ?)",
                    (resource["id"], note.get("text")),
                )

        elif kind == "Goal":
            connection.execute(
                "INSERT INTO goals VALUES (?, ?, ?, ?)",
                (resource["id"], patient_id, resource.get("lifecycleStatus"), resource.get("description", {}).get("text")),
            )
            for target in resource.get("target", []):
                connection.execute(
                    "INSERT INTO goal_targets(goal_id, measure, due_date) VALUES (?, ?, ?)",
                    (resource["id"], target.get("measure", {}).get("text"), target.get("dueDate")),
                )

        elif kind == "CarePlan":
            period = resource.get("period", {})
            connection.execute(
                "INSERT INTO care_plans VALUES (?, ?, ?, ?, ?, ?)",
                (resource["id"], patient_id, resource.get("status"), resource.get("intent"), period.get("start"), period.get("end")),
            )
            for category in resource.get("category", []):
                codings = category.get("coding", []) or [{}]
                for coding in codings:
                    connection.execute(
                        "INSERT INTO care_plan_categories(care_plan_id, system, code, display, category_text) VALUES (?, ?, ?, ?, ?)",
                        (resource["id"], coding.get("system"), coding.get("code"), coding.get("display"), category.get("text")),
                    )
            for goal in resource.get("goal", []):
                connection.execute(
                    "INSERT INTO care_plan_goals VALUES (?, ?)",
                    (resource["id"], referenced_id(goal.get("reference"), "Goal")),
                )
            for position, activity in enumerate(resource.get("activity", []), start=1):
                connection.execute(
                    "INSERT INTO care_plan_activities(care_plan_id, position, description) VALUES (?, ?, ?)",
                    (resource["id"], position, activity.get("detail", {}).get("description")),
                )

        elif kind == "CareTeam":
            scoped_patient_id = referenced_id(
                resource.get("subject", {}).get("reference"), "Patient"
            )
            group_id = next(
                group_id
                for group_id, group in patient_groups.items()
                if scoped_patient_id
                in {
                    referenced_id(member.get("entity", {}).get("reference"), "Patient")
                    for member in group.get("member", [])
                }
            )
            operational_team_id = f"careteam-{group_id.rsplit('-', 1)[-1]}"
            exists = connection.execute(
                "SELECT 1 FROM care_teams WHERE care_team_id = ?", (operational_team_id,)
            ).fetchone()
            if not exists:
                connection.execute(
                    "INSERT INTO care_teams VALUES (?, ?)",
                    (operational_team_id, resource.get("status")),
                )
                for participant in resource.get("participant", []):
                    roles = participant.get("role", []) or [{}]
                    for role in roles:
                        member = participant.get("member", {})
                        connection.execute(
                            "INSERT INTO care_team_clinicians VALUES (?, ?, ?)",
                            (
                                operational_team_id,
                                referenced_id(member.get("reference"), "Practitioner"),
                                role.get("text"),
                            ),
                        )
                for note in resource.get("note", []):
                    connection.execute(
                        "INSERT INTO care_team_notes(care_team_id, note_text) VALUES (?, ?)",
                        (operational_team_id, note.get("text")),
                    )
            connection.execute(
                "INSERT INTO care_team_patients VALUES (?, ?)",
                (operational_team_id, scoped_patient_id),
            )


def export_csv_tables(connection: sqlite3.Connection) -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    for stale_csv in CSV_DIR.glob("*.csv"):
        stale_csv.unlink()
    tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    for table in tables:
        cursor = connection.execute(f'SELECT * FROM "{table}"')
        with (CSV_DIR / f"{table}.csv").open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow([column[0] for column in cursor.description])
            writer.writerows(cursor.fetchall())


def main() -> None:
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))
    resources = [entry["resource"] for entry in bundle.get("entry", [])]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCHEMA_FILE.write_text(SCHEMA, encoding="utf-8")
    DATABASE.unlink(missing_ok=True)
    with sqlite3.connect(DATABASE) as connection:
        connection.executescript(SCHEMA)
        insert_resources(connection, resources)
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations: {violations}")
        export_csv_tables(connection)


if __name__ == "__main__":
    main()
