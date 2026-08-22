# Anchor data model

MongoDB is the local system of record. Relationships use stable domain IDs
(`patient_id`, `clinician_id`, `call_id`, and similar) rather than MongoDB
object IDs so records remain portable and auditable.

```mermaid
erDiagram
    CLINICIANS }|--o{ CARE_TEAMS : assigned
    CARE_TEAMS ||--|{ PATIENTS : supports
    PATIENTS ||--o{ CONDITIONS : has
    PATIENTS ||--o{ GOALS : owns
    GOALS ||--o{ GOAL_OBSERVATIONS : tracks
    PATIENTS ||--|| CARE_PLANS : follows
    CARE_PLANS ||--o{ CARE_PLAN_REVISIONS : versions

    PATIENTS ||--o{ CALLS : participates
    CALLS ||--o| VOICE_ANALYSES : generates
    CARE_TEAMS ||--o{ VOICE_ANALYSES : reviews
    CARE_PLANS ||--o{ VOICE_ANALYSES : guides
    VOICE_RISK_TIERS ||--o{ VOICE_ANALYSES : classifies
    CLINICIANS o|--o{ VOICE_ANALYSES : resolves

    REFERENCE_LIBRARY }o--o{ GOALS : supports
    CALLS ||--o{ MEMORIES : extracts
    CALLS ||--o{ ALERTS : raises
    PATIENTS ||--o{ SIGNALS : produces
    PATIENTS ||--o{ AUDIT_EVENTS : concerns
```

## Enforced invariants

- Each synthetic clinic patient belongs to `care-team-anchor-demo`, whose
  `clinician_ids` contains exactly two clinicians.
- Fixture initialization is versioned and idempotent: the canonical demo contains
  exactly 30 unique patients across Tier 3, Tier 2, Tier 1, and routine queues.
- Queue priority is derived from canonical risk fields and current action state;
  direct patient edits cannot overwrite the calculated risk tier.
- Patient, clinician, care-team, call, goal, reference, risk-tier, and voice
  analysis domain IDs are uniquely indexed.
- One active care-plan document is stored per patient for fast reads. Every
  publish also appends an immutable `(patient_id, version)` revision.
- Goal observations retain their event time and source. A goal's
  `miss_threshold` is evaluated inside its own `tracking_window_days`.
- A repeated goal miss opens one deduplicated Tier 2 pattern alert. Direct
  safety signals remain Tier 3 escalations.
- Each completed call produces at most one voice analysis linked to the
  patient, care team, plan version, and risk tier.
- Reference entries are ID-addressable, categorized, clinician-reviewed, and
  surfaced only when their keywords are relevant.
- Voice preference stores `voice_mode` and a catalog `voice_id`; personalized mode
  requires affirmative consent and never exposes the private reference artifact.
- Microphone events retain engine, frame count, and duration for audit evidence.
  Raw audio is processed in memory and is not persisted.

All repository fixtures are synthetic. This model is evidence for the demo;
it is not a substitute for a production clinical governance, retention, or
authorization design.
