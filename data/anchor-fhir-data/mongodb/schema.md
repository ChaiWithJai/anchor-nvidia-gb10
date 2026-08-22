# MongoDB document model

```mermaid
erDiagram
    CLINICIANS ||--o{ CARE_TEAMS : clinicianId
    CARE_TEAMS ||--|{ PATIENTS : "patientIds [exactly 2]"
    PATIENTS ||--o{ CONDITIONS : patientId
    PATIENTS ||--o{ GOALS : patientId
    PATIENTS ||--|| CARE_PLANS : patientId
    CARE_PLANS }o--o{ GOALS : goalIds

    CLINICIANS {
        string _id PK
        string displayName
        array givenNames
        string familyName
    }
    CARE_TEAMS {
        string _id PK
        string sourceGroupId FK
        array patientCareTeamIds FK
        string clinicianId FK
        array patientIds FK
        string status
        string clinicianRole
        array notes
    }
    PATIENTS {
        string _id PK
        array identifiers
        array names
        string gender
        string birthDate
        array addresses
        array tags
    }
    CONDITIONS {
        string _id PK
        string patientId FK
        object diagnosis
        object clinicalStatus
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
        string patientId FK
        string careTeamId FK
        string patientCareTeamId FK
        array goalIds FK
        array activities
        object period
    }
```

Arrays and value objects that are owned by a single document are embedded. Shared entities and independently queried clinical resources use string references based on their FHIR IDs.

The `careTeams` collection deliberately stays at the five-team operational grain. Each document combines one source FHIR `Group` (`sourceGroupId`) with the two patient-scoped FHIR `CareTeam` resources listed in `patientCareTeamIds`. A care plan stores both the operational `careTeamId` and its exact FHIR `patientCareTeamId`.
