# Anchor FHIR MongoDB — Team Lead ERD

```mermaid
erDiagram
    CLINICIANS ||--o{ CARE_TEAMS : "clinicianId — one clinician covers many teams"
    CARE_TEAMS ||--|{ PATIENTS : "patientIds — exactly 2 patients per team"

    PATIENTS ||--o{ CONDITIONS : patientId
    PATIENTS ||--o{ GOALS : patientId
    PATIENTS ||--|| CARE_PLANS : patientId
    CARE_PLANS }o--|{ GOALS : goalIds
    PATIENTS ||--|| HEALTH_HISTORIES : patientId
    CONDITIONS }o--o{ HEALTH_HISTORIES : "entries.relatedConditionIds"
    GOALS }o--o{ HEALTH_HISTORIES : "entries.relatedGoalIds"
    VOICE_RISK_TIERS ||--o{ HEALTH_HISTORIES : "entries.applicableTierId"

    PATIENTS ||--o{ VOICE_ANALYSES : patientId
    CARE_TEAMS ||--o{ VOICE_ANALYSES : careTeamId
    CARE_PLANS ||--o{ VOICE_ANALYSES : carePlanId
    VOICE_RISK_TIERS o|--o{ VOICE_ANALYSES : "riskAnalysis.tierId — null while pending"
    CLINICIANS o|--o{ VOICE_ANALYSES : "riskAnalysis.escalation.resolvedByClinicianId"

    PATIENTS {
        string _id PK
        array identifiers UK
        array names
        string gender
        string birthDate
        array telecom
        array addresses
        object maritalStatus
        array communications
        string employmentStatus
        array tags
    }

    CLINICIANS {
        string _id PK
        array givenNames
        string familyName
        string displayName
        array identifiers
        array telecom
        array qualifications
        array tags
    }

    CARE_TEAMS {
        string _id PK
        string sourceGroupId FK
        array patientCareTeamIds FK
        string clinicianId FK
        array patientIds FK
        array identifiers
        string name
        string status
        array categories
        object period
        array telecom
        string clinicianRole
        array notes
    }

    CONDITIONS {
        string _id PK
        string patientId FK
        object clinicalStatus
        object verificationStatus
        array categories
        object diagnosis
        string onsetDateTime
        array notes
    }

    GOALS {
        string _id PK
        string patientId FK
        string lifecycleStatus
        string description
        array targets
    }

    CARE_PLANS {
        string _id PK
        string patientId FK, UK
        string authorClinicianId FK
        string careTeamId FK
        string patientCareTeamId FK
        array conditionIds FK
        array identifiers
        string title
        string description
        string status
        string intent
        string created
        array categories
        object period
        array goalIds FK
        array activities
    }

    HEALTH_HISTORIES {
        string _id PK
        string patientId FK, UK
        string asOfDate
        boolean synthetic
        array entries
    }

    VOICE_RISK_TIERS {
        string _id PK
        int rank UK
        string label
        string disposition
        object action
        array eligibleReferenceCategories
        array patientFacingReferenceIds
        array clinicianOnlyReferenceIds
        object escalationRule
        boolean terminal
        array keywordSignals
    }

    VOICE_ANALYSES {
        string _id PK
        string patientId FK
        string careTeamId FK
        string carePlanId FK
        string pipelineStage
        object call
        object inputAudio
        object acousticAnalysis
        object transcription
        object riskAnalysis
        object guidance
        object alert
        object responseAudio
        date createdAt
        date updatedAt
    }
```

## Embedded voice-analysis structure

```mermaid
flowchart LR
    VA[VOICE_ANALYSES] --> CALL[call<br/>inbound source + timestamps]
    VA --> INPUT[inputAudio<br/>raw WAV drive URI + metadata]
    VA --> ACOUSTIC[acousticAnalysis<br/>Kokoro features]
    VA --> TRANSCRIPT[transcription<br/>faster-whisper text]
    VA --> RISK[riskAnalysis<br/>NemoClaw + Qwen 27B]
    VA --> GUIDANCE[guidance<br/>recovery response text]
    VA --> ALERT[alert<br/>team review + escalation]
    VA --> OUTPUT[responseAudio<br/>Kokoro WAV + playback]

    RISK --> PATTERN[patternEvidence<br/>recurrence + missed goals + safety]
    RISK --> ACTION[action<br/>name + gate + status]
    RISK --> REFERENCES[referenceUsage<br/>patient-facing vs clinician-only]
    RISK --> ESCALATION[escalation<br/>terminal + clinician resolution]
```

## Cardinality and enforcement notes

| Rule | Enforcement |
|---|---|
| Five care teams total | Seed validation and tests |
| FHIR patient-scoped CareTeams | Each MongoDB team projects two patient CareTeams identified by `patientCareTeamIds` |
| Two unique patients per team | `careTeams` JSON Schema uses `minItems: 2`, `maxItems: 2`, and `uniqueItems: true` |
| One team per patient | Unique multikey index on `careTeams.patientIds` |
| One clinician per team | Required scalar `careTeams.clinicianId` |
| One clinician may cover many teams | Non-unique index on `careTeams.clinicianId` |
| One care plan per patient | Unique index on `carePlans.patientId` |
| One health history per patient | Unique index on `healthHistories.patientId` |
| Lifestyle history remains non-diagnostic | Entries link back to authoritative FHIR condition and goal IDs |
| Tier 1 is ungated | `voiceRiskTiers/tier-1-mild` configuration and integration tests |
| Tier 2 is OpenShell-gated | `voiceRiskTiers/tier-2-moderate` configuration and integration tests |
| Tier 3 is always-open and terminal | `voiceRiskTiers/tier-3-at-risk` configuration and clinician-resolution tests |
| MongoDB references exist | Generator and integration tests; MongoDB itself does not enforce foreign keys |

## Review decisions

1. Patient identifiers remain FHIR string IDs instead of MongoDB `ObjectId` values to preserve interoperability.
2. Reusable clinical resources are separate collections; fields owned by one record are embedded subdocuments.
3. Each voice interaction is an append-oriented document referencing the patient, current care team, care plan, and selected risk-tier policy.
4. Keyword lists are review signals only. NemoClaw/Qwen performs the classification using context, recurrence, ambiguity, and safety evidence.
5. Tier 3 cannot self-resolve; clinician identity and resolution timestamps are stored in `riskAnalysis.escalation`.
6. Names, addresses, phone numbers, email addresses, team operations, and clinician credentials are deterministic synthetic demo values; none should be treated as real identity or contact data.
7. The five MongoDB care-team documents are operational projections. In source FHIR, five Groups define the rosters and ten patient-scoped CareTeams satisfy the one-patient CareTeam subject model.
