# Anchor FHIR + MongoDB data package

This folder is designed to be copied into an existing Git repository as a self-contained data module.

It contains deterministic synthetic behavioral-health data, FHIR R4 bundles, MongoDB collections and validators, normalized SQLite/CSV outputs, ERDs, generators, and tests. It contains no real patient data.

## Recommended repository location

Copy this entire folder to:

```text
your-existing-repository/
└── data/
    └── anchor-fhir-data/
```

Keeping the module under `data/` makes its purpose clear and avoids mixing generated clinical fixtures with application source code.

## Contents

```text
anchor-fhir-data/
├── README.md
├── summary.md
├── generate_fhir_ehr.py
├── generate_mongodb.py
├── normalize_fhir.py
├── bundle-patient-01.json ... bundle-patient-10.json
├── bundle-care-teams.json
├── combined-patient-bundles.json
├── mongodb/
│   ├── schema.mongodb.js
│   ├── seed.mongodb.js
│   ├── collections/
│   ├── tests/
│   └── documentation files
└── normalized/
    ├── schema.sql
    ├── normalized-fhir.sqlite
    ├── tables/
    └── erd.md
```

## Requirements

- Python 3.9 or newer
- Node.js for JavaScript syntax checks
- MongoDB Community Server or MongoDB Atlas
- `mongosh` for loading and testing MongoDB

The Python generators use only the standard library. No Python package installation is required.

## Quick start

From this folder, regenerate every derived artifact:

```bash
python3 generate_fhir_ehr.py
python3 generate_mongodb.py
python3 normalize_fhir.py
```

Run offline data and syntax tests:

```bash
./mongodb/tests/run_tests.sh
```

Load the schema and seed data into a local MongoDB database:

```bash
mongosh mongodb://localhost:27017 --file mongodb/schema.mongodb.js
mongosh mongodb://localhost:27017 --file mongodb/seed.mongodb.js
```

The scripts use the database name `anchor_fhir`.

Run the complete MongoDB integration suite:

```bash
RUN_MONGODB_INTEGRATION=1 ./mongodb/tests/run_tests.sh
```

For Atlas or another MongoDB deployment:

```bash
MONGODB_URI="mongodb+srv://YOUR_CONNECTION_STRING" \
RUN_MONGODB_INTEGRATION=1 \
./mongodb/tests/run_tests.sh
```

Do not commit a real connection string or credentials. Supply them through repository secrets or environment variables.

## Application integration

The application-facing collections are:

- `patients`
- `clinicians`
- `careTeams`
- `conditions`
- `goals`
- `carePlans`
- `healthHistories`
- `voiceRiskTiers`
- `voiceAnalyses`, created by the schema for runtime call records

Use the MongoDB `_id` string values as stable references. In particular:

- `carePlans.careTeamId` points to one of five operational MongoDB teams.
- `carePlans.patientCareTeamId` points to the exact patient-scoped FHIR CareTeam.
- `careTeams.sourceGroupId` identifies the FHIR Group representing the operational roster.
- `careTeams.patientCareTeamIds` contains exactly two patient-scoped FHIR CareTeam IDs.

## Optional package scripts

If the host repository uses npm, these entries can be added to its `package.json` scripts section. Adjust the folder prefix if you install the module somewhere other than `data/anchor-fhir-data`.

```json
{
  "scripts": {
    "data:generate": "cd data/anchor-fhir-data && python3 generate_fhir_ehr.py && python3 generate_mongodb.py && python3 normalize_fhir.py",
    "data:test": "data/anchor-fhir-data/mongodb/tests/run_tests.sh",
    "data:seed": "mongosh ${MONGODB_URI:-mongodb://localhost:27017} --file data/anchor-fhir-data/mongodb/schema.mongodb.js && mongosh ${MONGODB_URI:-mongodb://localhost:27017} --file data/anchor-fhir-data/mongodb/seed.mongodb.js"
  }
}
```

## CI example

An offline CI check does not require a running MongoDB server:

```yaml
- name: Validate Anchor synthetic data
  run: ./data/anchor-fhir-data/mongodb/tests/run_tests.sh
```

For database integration tests, start MongoDB as a CI service and set `RUN_MONGODB_INTEGRATION=1`.

## Editing rules

1. Change generator or seed-source files rather than editing generated JSON or CSV files alone.
2. Run all three generators after a model change.
3. Run the offline tests before committing.
4. Run MongoDB integration tests whenever collection schemas or references change.
5. Keep all data synthetic. Never add real PHI, credentials, production audio, or production storage URIs.

## Data model

The model contains five operational teams, exactly two patients per team, two clinicians total, and one clinician assigned to each team. In FHIR, each patient has an individual CareTeam, while Groups preserve the five-team operational roster. MongoDB projects those resources back into five application-friendly care-team documents.

See [summary.md](summary.md) for the complete data dictionary and [mongodb/team-lead-erd.md](mongodb/team-lead-erd.md) for the MongoDB ERD.

## Compliance boundary

This package supports development and demonstrations; it does not make an application HIPAA-compliant or certify full FHIR/US Core conformance. Production use requires organizational policies, access controls, audit logging, encryption, consent handling, retention controls, approved profiles, terminology validation, and review with the applicable compliance and clinical teams.
