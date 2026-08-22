# Anchor synthetic health data summary

## Purpose and scope

This directory contains deterministic, entirely synthetic behavioral-health and substance-use recovery data for demonstrations, development, and automated testing. It is not a production EHR, does not contain real PHI, and must not be used to make clinical decisions.

The source of truth is the generated FHIR R4 collection in `combined-patient-bundles.json`. MongoDB documents and normalized SQLite/CSV tables are derived projections for application queries and analysis.

## Dataset at a glance

| Layer | Entity | Count | Definition |
|---|---:|---:|---|
| FHIR | Patient | 10 | Synthetic person receiving recovery care |
| FHIR | Condition | 11 | Active, confirmed SUD diagnosis coded with ICD-10-CM |
| FHIR | Goal | 10 | Patient-specific recovery outcome with target date |
| FHIR | CarePlan | 10 | Clinician-authored recovery plan; one per patient |
| FHIR | CareTeam | 10 | Patient-scoped clinical team; one per patient |
| FHIR | Group | 5 | Operational two-patient cohort representing one business care team |
| FHIR | Practitioner | 2 | Synthetic clinicians assigned across the five operational teams |
| MongoDB | careTeams | 5 | Application projection combining one Group and two patient CareTeams |
| MongoDB | healthHistories | 10 | One longitudinal psychosocial history document per patient |
| MongoDB | voiceRiskTiers | 3 | Behavioral routing rules for mild, moderate, and at-risk interactions |

The combined FHIR bundle therefore contains 58 resources.

## Recommended care-team model

The business requirement remains five teams, two patients per team, and one clinician per team. FHIR and the application represent this at different grains:

```text
Operational team (FHIR Group / MongoDB careTeams)
  ├── Patient A ── Patient-scoped FHIR CareTeam ── Clinician
  └── Patient B ── Patient-scoped FHIR CareTeam ── Clinician
```

- A FHIR `Group` is the operational roster and contains exactly two Patient references.
- A FHIR `CareTeam` has exactly one Patient subject and one Practitioner participant.
- Both patient CareTeams carry the same `urn:anchor:operational-care-team` identifier as their Group.
- A `CarePlan.careTeam` points to the CareTeam whose subject is the same patient.
- MongoDB collapses the Group and its two patient CareTeams into one query-friendly `careTeams` document.

This preserves five operational teams without using a Group as the subject of a patient-facing CareTeam.

## Cardinality and integrity rules

| Relationship | Rule |
|---|---|
| Operational Group → Patient | Exactly 2 unique patients |
| Patient → operational Group | Exactly 1 group |
| Patient → patient CareTeam | Exactly 1 CareTeam |
| Patient CareTeam → Practitioner | Exactly 1 clinician participant |
| Practitioner → operational team | One-to-many; clinician 01 covers 3 teams and clinician 02 covers 2 |
| Patient → CarePlan | Exactly 1 in this seeded dataset |
| CarePlan → Goal | One or more |
| CarePlan → Condition | One or more through `addresses` |
| Patient → healthHistories | Exactly 1 MongoDB history document |

All generated FHIR references must resolve globally. CarePlan, Goal, Condition, and CareTeam patient references must agree.

## FHIR resource definitions

### Patient

Contains a synthetic MRN, official name, administrative gender, birth date, address, phone, email, marital status, preferred language, and an Anchor employment-status extension. Each patient is tagged as synthetic under `meta.tag`.

### Condition

Represents an active and confirmed SUD problem-list item. Diagnoses use ICD-10-CM. The onset date and a clinical severity note are included. Patient 04 has two Conditions because alcohol and opioid disorders are modeled separately.

### Goal

Represents a patient-specific recovery objective. It includes lifecycle status, description, measurement text, and target due date.

### CarePlan

Represents the clinician-authored recovery plan. It includes status, intent, assessment-plan category, patient, authoring Practitioner, patient CareTeam, addressed Conditions, linked Goals, plan period, scheduled activities, and a safety-boundary note.

### CareTeam

Represents the clinical team for one patient. Its `subject` is a Patient reference and its participant is a Practitioner reference. The operational-team identifier links it back to the corresponding Group and MongoDB care-team projection.

### Group

Represents one operational care-team patient cohort. It contains exactly two Patient members and carries the shared operational-team identifier. A Group is not treated as the subject of a US Core-style patient CareTeam.

### Practitioner

Represents one synthetic clinician with a fictional license identifier, work contact information, and synthetic qualification coding.

## Identifier systems

| System | Use |
|---|---|
| `urn:anchor:demo-mrn` | Synthetic patient record number |
| `urn:anchor:demo-care-plan` | Synthetic care-plan identifier |
| `urn:anchor:demo-patient-care-team` | Unique patient CareTeam identifier |
| `urn:anchor:operational-care-team` | Shared key connecting Group, patient CareTeams, and MongoDB team |
| `urn:anchor:synthetic-clinician-license` | Fictional clinician license |
| `urn:anchor:demo-data` | Synthetic-data tag |

## MongoDB collection definitions

| Collection | Grain and purpose |
|---|---|
| `patients` | One patient per document; demographic projection of Patient |
| `clinicians` | One clinician per document; projection of Practitioner |
| `careTeams` | One operational team per document; includes `sourceGroupId`, two `patientCareTeamIds`, two `patientIds`, and one `clinicianId` |
| `conditions` | One Condition per document, linked by `patientId` |
| `goals` | One Goal per document, linked by `patientId` |
| `carePlans` | One plan per document; `careTeamId` is the operational team and `patientCareTeamId` is the exact FHIR CareTeam reference |
| `healthHistories` | One patient history document with embedded chronological psychosocial observations |
| `voiceRiskTiers` | Reference documents controlling response and escalation behavior |

The MongoDB model embeds values owned by one aggregate and stores IDs for shared or independently queried entities. MongoDB validators are defined in `mongodb/schema.mongodb.js`.

## Health-history definition

Health-history entries generalize lifestyle and psychosocial factors across sleep and routine, nutrition, social isolation, family relationships, employment, housing, finances, emotional coping, cognition, distress tolerance, and H.A.L.T. triggers. Entries include observation dates, severity, recurrence, evidence source, related Conditions and Goals, recommended reference-library content, and the applicable voice-risk tier.

These entries are synthetic behavioral context. They are not additional diagnoses and do not replace clinician assessment.

## Voice-risk definition

- Tier 1 handles mild, in-conversation needs with approved patient-facing reference material.
- Tier 2 represents a repeated or compounding pattern and flags it for clinician review through the gated workflow.
- Tier 3 represents at-risk content and immediately routes to a clinician; seeded patient histories intentionally contain no fabricated Tier 3 event.

The risk tier is an application behavior rule, not a FHIR clinical diagnosis.

## Terminology and conformance boundary

- Conditions use `http://hl7.org/fhir/sid/icd-10-cm`.
- CarePlan category uses the US Core `assess-plan` code.
- Clinical and verification statuses use HL7 terminology systems.
- Anchor-specific URNs are demo namespaces and require formal CodeSystem or StructureDefinition publication before production use.
- The generator checks counts, uniqueness, cardinalities, reference resolution, and patient consistency.
- The data has not been certified by the official HL7 validator or a terminology server and does not claim full US Core conformance.
- Production use would additionally require approved profiles, provenance, consent, audit events, security labels, access controls, encryption, retention rules, and organization-specific HIPAA policies.

## Regeneration and tests

Run from the repository root:

```bash
python3 "example data/generate_fhir_ehr.py"
python3 "example data/generate_mongodb.py"
python3 "example data/normalize_fhir.py"
python3 -m unittest discover -s "example data/mongodb/tests" -p "test_generated_data.py" -v
```

The generators are deterministic. Edit the generator or seed source, not only a generated JSON/CSV file, or the next regeneration will overwrite the manual change.
