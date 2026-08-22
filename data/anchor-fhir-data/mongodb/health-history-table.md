# Synthetic patient health-history table

The existing FHIR `Condition` resources remain the authoritative diagnoses. The items below are synthetic, non-diagnostic lifestyle and psychosocial history entries used to demonstrate longitudinal recovery support.

| Patient | Existing FHIR condition(s) | Seeded lifestyle and psychosocial history | Pattern tier |
|---|---|---|---|
| `patient-01` | Alcohol dependence | Sleep fragmentation; work-related anxiety trigger; low distress tolerance | Tier 1 |
| `patient-02` | Opioid dependence | Lack of daily structure; irregular meals; treatment/work scheduling pressure | Tier 1 |
| `patient-03` | Cocaine abuse | Recurring peer-group vulnerability; sober social anxiety; unstructured weekends | Tier 2 for the recurring peer trigger |
| `patient-04` | Alcohol and opioid dependence | Family strain; financial pressure; executive-function burden | Tier 1 |
| `patient-05` | Alcohol dependence | Financial instability; family trust strain; H.A.L.T. tiredness | Tier 1 |
| `patient-06` | Opioid dependence | Recurring appointment barrier; scheduling difficulty; fatigue | Tier 2 for the recurring attendance pattern |
| `patient-07` | Cannabis abuse | Emotional flatness; social isolation; sober social anxiety | Tier 1 |
| `patient-08` | Stimulant dependence | Sleep fragmentation; nutritional inconsistency; executive dysfunction | Tier 1 |
| `patient-09` | Alcohol abuse | Recurring loneliness; work anxiety; unstructured weeknights | Tier 2 for the recurring loneliness pattern |
| `patient-10` | Alcohol dependence | Program-access gap; limited support during intake wait; transition anxiety | Tier 1 |

## MongoDB document fields

Collection: `healthHistories` — one document per patient.

| Field | Type | Purpose |
|---|---|---|
| `_id` | String | Health-history document identifier |
| `patientId` | String | Unique reference to `patients._id` |
| `asOfDate` | Date string | History snapshot date |
| `synthetic` | Boolean | Must be `true` for this demo dataset |
| `entries[].historyEntryId` | String | Stable history-entry identifier |
| `entries[].domain` | Enum | One of five lifestyle/psychosocial domains |
| `entries[].issueCode` | Enum | Generalized issue code |
| `entries[].status` | Enum | Active, monitoring, improving, or resolved |
| `entries[].severity` | Enum | Mild, moderate, or severe history descriptor |
| `entries[].firstObservedDate` | Date string | First synthetic observation date |
| `entries[].lastObservedDate` | Date string | Most recent synthetic observation date |
| `entries[].evidenceSource` | Enum | Patient report, check-in, pattern, plan review, or clinician documentation |
| `entries[].summary` | String | Plain-language, non-diagnostic description |
| `entries[].occurrenceCount` | Integer | Number of recorded occurrences |
| `entries[].consecutiveCheckIns` | Integer | Consecutive check-ins supporting pattern escalation |
| `entries[].relatedConditionIds` | String array | Links to authoritative FHIR-derived conditions |
| `entries[].relatedGoalIds` | String array | Links to patient recovery goals |
| `entries[].recommendedReferenceIds` | String array | Allowed coping or psychoeducation references |
| `entries[].applicableTierId` | String | Tier suggested by the stored pattern evidence |

Tier assignment is contextual. A lifestyle issue is not itself a diagnosis or automatic risk classification. Tier 2 is seeded only where the same pattern appears across three consecutive check-ins; no Tier 3 event was fabricated.
