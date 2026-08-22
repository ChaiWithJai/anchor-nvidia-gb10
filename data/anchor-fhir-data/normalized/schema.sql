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
