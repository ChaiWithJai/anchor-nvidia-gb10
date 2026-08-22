# Voice analysis collection

Collection: `voiceAnalyses`

One document represents one inbound patient call or seeded `.wav` interaction.

| Field | MongoDB type | Required | Produced by / purpose |
|---|---|---:|---|
| `_id` | String | Yes | Unique interaction ID |
| `patientId` | String | Yes | Reference to `patients._id` |
| `careTeamId` | String | Yes | Reference to `careTeams._id` |
| `carePlanId` | String | Yes | Recovery plan used for guidance |
| `pipelineStage` | Enum | Yes | Current end-to-end processing stage |
| `call.direction` | Enum | Yes | Locked to `inbound` |
| `call.source` | Enum | Yes | `patient_call` or `seeded_wav` |
| `call.receivedAt` | Date | Yes | Ingest timestamp |
| `call.completedAt` | Date/null | No | Call completion timestamp |
| `inputAudio.driveUri` | String | Yes | URI for the raw `.wav` in drive storage |
| `inputAudio.mimeType` | Enum | Yes | WAV media type |
| `inputAudio.sha256` | String/null | No | Integrity and deduplication hash |
| `inputAudio.durationMs` | Number/null | No | Audio duration |
| `inputAudio.sampleRateHz` | Number/null | No | WAV sample rate |
| `inputAudio.channels` | Number/null | No | Audio channel count |
| `acousticAnalysis.status` | Enum | Yes | Kokoro processing state |
| `acousticAnalysis.engine` | Enum | Yes | Locked to `Kokoro` |
| `acousticAnalysis.features` | Object | Yes | Acoustic wave measurements |
| `acousticAnalysis.features.speechRateWpm` | Number/null | No | Estimated speech rate |
| `acousticAnalysis.features.meanPitchHz` | Number/null | No | Mean fundamental frequency |
| `acousticAnalysis.features.pitchStdDevHz` | Number/null | No | Pitch variability |
| `acousticAnalysis.features.rmsEnergy` | Number/null | No | Signal energy |
| `acousticAnalysis.features.silenceRatio` | Number/null | No | Fraction of audio classified as silence, 0–1 |
| `acousticAnalysis.features.jitterPercent` | Number/null | No | Cycle-to-cycle pitch variation |
| `acousticAnalysis.features.shimmerPercent` | Number/null | No | Cycle-to-cycle amplitude variation |
| `transcription.status` | Enum | Yes | Transcription processing state |
| `transcription.engine` | Enum | Yes | Locked to `faster-whisper` |
| `transcription.text` | String/null | Yes | Normalized voice transcript |
| `transcription.language` | String/null | No | Detected language |
| `transcription.confidence` | Number/null | No | Confidence from 0–1 |
| `riskAnalysis.status` | Enum | Yes | Reasoning processing state |
| `riskAnalysis.orchestrator` | Enum | Yes | Locked to `NemoClaw` |
| `riskAnalysis.model` | Enum | Yes | Locked to `Qwen 27B` |
| `riskAnalysis.tierId` | Enum/null | Yes | `tier-1-mild`, `tier-2-moderate`, or `tier-3-at-risk` |
| `riskAnalysis.tierRank` | Integer/null | Yes | Ordered tier rank: 1, 2, or 3 |
| `riskAnalysis.rationale` | String/null | Yes | Reviewable risk explanation |
| `riskAnalysis.indicators` | String array | Yes | Detected risk indicators |
| `riskAnalysis.patternEvidence.sameTriggerKey` | String/null | Yes | Stable key for recurrence tracking across check-ins |
| `riskAnalysis.patternEvidence.consecutiveCheckIns` | Integer | Yes | Consecutive check-ins containing the same trigger |
| `riskAnalysis.patternEvidence.missedGoalTargets` | Integer | Yes | Goal misses in the current tracking window |
| `riskAnalysis.patternEvidence.ambiguousResponse` | Boolean | Yes | Current response cannot be classified confidently |
| `riskAnalysis.patternEvidence.safetyRelevant` | Boolean | Yes | Current response contains a safety-relevant disclosure |
| `riskAnalysis.patternEvidence.logicalCoherenceConcern` | Boolean | Yes | Current response does not track logically |
| `riskAnalysis.action.name` | Enum/null | Yes | Tier action selected by NemoClaw/Qwen |
| `riskAnalysis.action.gated` | Boolean | Yes | True only for the Tier 2 OpenShell action |
| `riskAnalysis.action.gate` | Enum/null | Yes | `OpenShell` for Tier 2; otherwise null |
| `riskAnalysis.action.status` | Enum | Yes | Pending, awaiting gate, executed, or failed |
| `riskAnalysis.referenceUsage.surfacedPatientFacingReferenceIds` | String array | Yes | Allowed Tier 1/2 coping and psychoeducation references actually surfaced |
| `riskAnalysis.referenceUsage.clinicianOnlyReferenceIds` | String array | Yes | Tier 3 crisis references shown only in the clinician escalation record |
| `riskAnalysis.referenceUsage.upstreamProgramResourceId` | String/null | Yes | Program resource selected upstream from the Recovery Plan, never reactively |
| `riskAnalysis.escalation.terminal` | Boolean | Yes | True for Tier 3 |
| `riskAnalysis.escalation.resolved` | Boolean | Yes | Tier 3 resolution state controlled by a clinician |
| `riskAnalysis.escalation.resolvedByClinicianId` | String/null | Yes | Clinician who closed the escalation |
| `riskAnalysis.escalation.resolvedAt` | Date/null | Yes | Clinician resolution timestamp |
| `guidance.referenceLibraryVersion` | String/null | Yes | Reference-library version used |
| `guidance.responseText` | String/null | Yes | Personalized recovery guidance |
| `alert.required` | Boolean | Yes | True for Tier 2 pattern flags and Tier 3 immediate escalations |
| `alert.status` | Enum | Yes | Dashboard and clinical escalation state |
| `alert.careTeamAlertedAt` | Date/null | No | Dashboard alert timestamp |
| `alert.reviewedBy` | String/null | No | OpenShell reviewer ID |
| `alert.reviewedAt` | Date/null | No | Review timestamp |
| `alert.escalatedToClinicianAt` | Date/null | No | Direct clinical escalation timestamp |
| `responseAudio.status` | Enum | Yes | Synthesis/playback state |
| `responseAudio.engine` | Enum | Yes | Locked to `Kokoro` |
| `responseAudio.driveUri` | String/null | Yes | URI for the rendered response `.wav` |
| `responseAudio.renderedAt` | Date/null | No | Synthesis completion timestamp |
| `responseAudio.playedAt` | Date/null | No | Playback timestamp |
| `createdAt` | Date | Yes | Document creation time |
| `updatedAt` | Date | Yes | Last pipeline update time |

Tier 1 is ungated and normally resolves within the call. Tier 2 executes `flag_pattern_for_clinician()` through OpenShell. Tier 3 executes `escalate_to_clinician()` immediately through an always-open path and cannot self-resolve; only a clinician may close it. Keywords are stored as human-review signals and must never be used as the classifier by themselves.
