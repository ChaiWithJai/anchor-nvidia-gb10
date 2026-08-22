const anchorDb = db.getSiblingDB("anchor_fhir");

function ensureCollection(name, validator) {
  const exists = anchorDb.getCollectionInfos({ name }).length > 0;
  if (exists) {
    anchorDb.runCommand({ collMod: name, validator, validationLevel: "strict", validationAction: "error" });
  } else {
    anchorDb.createCollection(name, { validator, validationLevel: "strict", validationAction: "error" });
  }
}

ensureCollection("patients", {
  $jsonSchema: {
    bsonType: "object",
    required: [
      "_id", "resourceType", "identifiers", "names", "gender", "birthDate",
      "telecom", "addresses", "maritalStatus", "communications", "employmentStatus", "tags"
    ],
    properties: {
      _id: { bsonType: "string", pattern: "^patient-[0-9]{2}$" },
      resourceType: { enum: ["Patient"] },
      identifiers: { bsonType: "array", minItems: 1 },
      names: { bsonType: "array", minItems: 1 },
      gender: { bsonType: "string" },
      birthDate: { bsonType: "string", pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" },
      telecom: { bsonType: "array", minItems: 2 },
      addresses: { bsonType: "array", minItems: 1 },
      maritalStatus: { bsonType: "object" },
      communications: { bsonType: "array", minItems: 1 },
      employmentStatus: {
        enum: ["employed_full_time", "employed_part_time", "unemployed", "student_part_time"]
      },
      tags: { bsonType: "array" }
    }
  }
});

ensureCollection("clinicians", {
  $jsonSchema: {
    bsonType: "object",
    required: [
      "_id", "resourceType", "givenNames", "familyName", "displayName",
      "identifiers", "telecom", "qualifications"
    ],
    properties: {
      _id: { bsonType: "string", pattern: "^clinician-[0-9]{2}$" },
      resourceType: { enum: ["Practitioner"] },
      givenNames: { bsonType: "array", minItems: 1, items: { bsonType: "string" } },
      familyName: { bsonType: "string" },
      displayName: { bsonType: "string" },
      identifiers: { bsonType: "array", minItems: 1 },
      telecom: { bsonType: "array", minItems: 2 },
      qualifications: { bsonType: "array", minItems: 1 },
      tags: { bsonType: "array" }
    }
  }
});

ensureCollection("careTeams", {
  $jsonSchema: {
    bsonType: "object",
    required: [
      "_id", "resourceType", "name", "status", "identifiers", "categories",
      "period", "telecom", "sourceGroupId", "patientCareTeamIds", "patientIds",
      "clinicianId", "clinicianRole", "notes"
    ],
    properties: {
      _id: { bsonType: "string", pattern: "^careteam-[0-9]{2}$" },
      resourceType: { enum: ["CareTeam"] },
      sourceGroupId: { bsonType: "string", pattern: "^patient-group-[0-9]{2}$" },
      patientCareTeamIds: {
        bsonType: "array",
        minItems: 2,
        maxItems: 2,
        uniqueItems: true,
        items: { bsonType: "string", pattern: "^careteam-patient-[0-9]{2}$" }
      },
      name: { bsonType: "string" },
      status: { bsonType: "string" },
      identifiers: { bsonType: "array", minItems: 1 },
      categories: { bsonType: "array", minItems: 1 },
      period: { bsonType: "object" },
      telecom: { bsonType: "array", minItems: 1 },
      patientIds: {
        bsonType: "array",
        minItems: 2,
        maxItems: 2,
        uniqueItems: true,
        items: { bsonType: "string", pattern: "^patient-[0-9]{2}$" }
      },
      clinicianId: { bsonType: "string", pattern: "^clinician-[0-9]{2}$" },
      clinicianRole: { bsonType: "string" },
      notes: { bsonType: "array", items: { bsonType: "string" } }
    }
  }
});

ensureCollection("conditions", {
  $jsonSchema: {
    bsonType: "object",
    required: ["_id", "resourceType", "patientId", "diagnosis"],
    properties: {
      _id: { bsonType: "string" },
      resourceType: { enum: ["Condition"] },
      patientId: { bsonType: "string", pattern: "^patient-[0-9]{2}$" },
      clinicalStatus: { bsonType: "object" },
      verificationStatus: { bsonType: "object" },
      categories: { bsonType: "array" },
      diagnosis: { bsonType: "object" },
      onsetDateTime: { bsonType: "string" },
      notes: { bsonType: "array", items: { bsonType: "string" } }
    }
  }
});

ensureCollection("goals", {
  $jsonSchema: {
    bsonType: "object",
    required: ["_id", "resourceType", "patientId", "lifecycleStatus", "description", "targets"],
    properties: {
      _id: { bsonType: "string" },
      resourceType: { enum: ["Goal"] },
      patientId: { bsonType: "string", pattern: "^patient-[0-9]{2}$" },
      lifecycleStatus: { bsonType: "string" },
      description: { bsonType: "string" },
      targets: { bsonType: "array" }
    }
  }
});

ensureCollection("carePlans", {
  $jsonSchema: {
    bsonType: "object",
    required: [
      "_id", "resourceType", "patientId", "identifiers", "title", "description",
      "status", "intent", "created", "authorClinicianId", "careTeamId",
      "patientCareTeamId", "conditionIds", "goalIds", "activities", "notes"
    ],
    properties: {
      _id: { bsonType: "string" },
      resourceType: { enum: ["CarePlan"] },
      patientId: { bsonType: "string", pattern: "^patient-[0-9]{2}$" },
      identifiers: { bsonType: "array", minItems: 1 },
      title: { bsonType: "string" },
      description: { bsonType: "string" },
      status: { bsonType: "string" },
      intent: { bsonType: "string" },
      created: { bsonType: "string", pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" },
      authorClinicianId: { bsonType: "string", pattern: "^clinician-[0-9]{2}$" },
      careTeamId: { bsonType: "string", pattern: "^careteam-[0-9]{2}$" },
      patientCareTeamId: { bsonType: "string", pattern: "^careteam-patient-[0-9]{2}$" },
      conditionIds: { bsonType: "array", minItems: 1, items: { bsonType: "string" } },
      categories: { bsonType: "array" },
      period: { bsonType: "object" },
      goalIds: { bsonType: "array", minItems: 1, items: { bsonType: "string" } },
      activities: { bsonType: "array", minItems: 1 },
      notes: { bsonType: "array", minItems: 1, items: { bsonType: "string" } }
    }
  }
});

ensureCollection("healthHistories", {
  $jsonSchema: {
    bsonType: "object",
    required: ["_id", "patientId", "asOfDate", "synthetic", "entries"],
    properties: {
      _id: { bsonType: "string", pattern: "^health-history-patient-[0-9]{2}$" },
      patientId: { bsonType: "string", pattern: "^patient-[0-9]{2}$" },
      asOfDate: { bsonType: "string", pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" },
      synthetic: { enum: [true] },
      entries: {
        bsonType: "array",
        minItems: 1,
        items: {
          bsonType: "object",
          required: [
            "historyEntryId", "domain", "issueCode", "status", "severity",
            "firstObservedDate", "lastObservedDate", "evidenceSource", "summary",
            "occurrenceCount", "consecutiveCheckIns", "relatedConditionIds",
            "relatedGoalIds", "recommendedReferenceIds", "applicableTierId"
          ],
          properties: {
            historyEntryId: { bsonType: "string" },
            domain: {
              enum: [
                "routine_sleep_biological",
                "social_environment_isolation",
                "employment_housing_financial",
                "emotional_psychological",
                "high_risk_lifestyle_trigger"
              ]
            },
            issueCode: {
              enum: [
                "sleep_fragmentation",
                "lack_daily_structure",
                "nutritional_depletion",
                "people_places_things_vulnerability",
                "relationship_family_strain",
                "social_anxiety_reengagement",
                "social_isolation",
                "financial_instability",
                "employment_disruption",
                "housing_insecurity",
                "program_access_gap",
                "appointment_adherence_barrier",
                "anhedonia_emotional_flatness",
                "low_distress_tolerance",
                "executive_dysfunction",
                "halt_hungry",
                "halt_angry_anxious",
                "halt_lonely",
                "halt_tired"
              ]
            },
            status: { enum: ["active", "monitoring", "improving", "resolved"] },
            severity: { enum: ["mild", "moderate", "severe"] },
            firstObservedDate: { bsonType: "string", pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" },
            lastObservedDate: { bsonType: "string", pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" },
            evidenceSource: {
              enum: ["patient_reported", "voice_check_in", "voice_pattern", "care_plan_review", "clinician_documented"]
            },
            summary: { bsonType: "string" },
            occurrenceCount: { bsonType: ["int", "long"], minimum: 1 },
            consecutiveCheckIns: { bsonType: ["int", "long"], minimum: 0 },
            relatedConditionIds: { bsonType: "array", items: { bsonType: "string" } },
            relatedGoalIds: { bsonType: "array", items: { bsonType: "string" } },
            recommendedReferenceIds: {
              bsonType: "array",
              items: {
                enum: [
                  "ref-coping-box-breathing",
                  "ref-coping-urge-surfing",
                  "ref-psychoed-craving-curve"
                ]
              }
            },
            applicableTierId: { enum: ["tier-1-mild", "tier-2-moderate", "tier-3-at-risk"] }
          }
        }
      }
    }
  }
});

ensureCollection("voiceRiskTiers", {
  $jsonSchema: {
    bsonType: "object",
    required: [
      "_id", "rank", "label", "disposition", "triggerSummary", "action",
      "eligibleReferenceCategories", "eligiblePatientFacingReferenceIds",
      "clinicianOnlyReferenceIds", "escalationRule", "terminal",
      "keywordSignals", "keywordPolicy"
    ],
    properties: {
      _id: { enum: ["tier-1-mild", "tier-2-moderate", "tier-3-at-risk"] },
      rank: { bsonType: ["int", "long"], minimum: 1, maximum: 3 },
      label: { enum: ["Mild", "Moderate", "At Risk"] },
      disposition: { enum: ["resolve_in_conversation", "flag_pattern", "escalate"] },
      triggerSummary: { bsonType: "string" },
      action: {
        bsonType: "object",
        required: ["name", "gated", "gate"],
        properties: {
          name: {
            enum: [
              "acknowledge_or_surface_reference",
              "flag_pattern_for_clinician",
              "escalate_to_clinician"
            ]
          },
          gated: { bsonType: "bool" },
          gate: { enum: [null, "OpenShell"] },
          alwaysOpen: { bsonType: "bool" }
        }
      },
      eligibleReferenceCategories: { bsonType: "array", items: { bsonType: "string" } },
      eligiblePatientFacingReferenceIds: { bsonType: "array", items: { bsonType: "string" } },
      clinicianOnlyReferenceIds: { bsonType: "array", items: { bsonType: "string" } },
      reactivelyExcludedCategories: { bsonType: "array", items: { bsonType: "string" } },
      escalationRule: { bsonType: "object" },
      terminal: { bsonType: "bool" },
      keywordSignals: { bsonType: "array", items: { bsonType: "string" } },
      keywordPolicy: { bsonType: "string" }
    }
  }
});

ensureCollection("voiceAnalyses", {
  $jsonSchema: {
    bsonType: "object",
    required: [
      "_id", "patientId", "careTeamId", "carePlanId", "pipelineStage",
      "call", "inputAudio", "acousticAnalysis", "transcription",
      "riskAnalysis", "guidance", "alert", "responseAudio",
      "createdAt", "updatedAt"
    ],
    properties: {
      _id: { bsonType: "string", pattern: "^voice-analysis-[A-Za-z0-9-]+$" },
      patientId: { bsonType: "string", pattern: "^patient-[0-9]{2}$" },
      careTeamId: { bsonType: "string", pattern: "^careteam-[0-9]{2}$" },
      carePlanId: { bsonType: "string", pattern: "^careplan-[0-9]{2}$" },
      pipelineStage: {
        enum: ["ingested", "analyzing", "transcribed", "reasoned", "alerted", "responded", "failed"]
      },
      call: {
        bsonType: "object",
        required: ["direction", "source", "receivedAt"],
        properties: {
          direction: { enum: ["inbound"] },
          source: { enum: ["patient_call", "seeded_wav"] },
          receivedAt: { bsonType: "date" },
          completedAt: { bsonType: ["date", "null"] }
        }
      },
      inputAudio: {
        bsonType: "object",
        required: ["driveUri", "mimeType"],
        properties: {
          driveUri: { bsonType: "string" },
          mimeType: { enum: ["audio/wav", "audio/x-wav"] },
          sha256: { bsonType: ["string", "null"] },
          durationMs: { bsonType: ["int", "long", "double", "null"], minimum: 0 },
          sampleRateHz: { bsonType: ["int", "long", "null"], minimum: 1 },
          channels: { bsonType: ["int", "long", "null"], minimum: 1 }
        }
      },
      acousticAnalysis: {
        bsonType: "object",
        required: ["status", "engine", "features"],
        properties: {
          status: { enum: ["pending", "completed", "failed"] },
          engine: { enum: ["Kokoro"] },
          engineVersion: { bsonType: ["string", "null"] },
          analyzedAt: { bsonType: ["date", "null"] },
          features: {
            bsonType: "object",
            properties: {
              speechRateWpm: { bsonType: ["int", "long", "double", "null"], minimum: 0 },
              meanPitchHz: { bsonType: ["int", "long", "double", "null"], minimum: 0 },
              pitchStdDevHz: { bsonType: ["int", "long", "double", "null"], minimum: 0 },
              rmsEnergy: { bsonType: ["int", "long", "double", "null"], minimum: 0 },
              silenceRatio: { bsonType: ["int", "long", "double", "null"], minimum: 0, maximum: 1 },
              jitterPercent: { bsonType: ["int", "long", "double", "null"], minimum: 0 },
              shimmerPercent: { bsonType: ["int", "long", "double", "null"], minimum: 0 }
            }
          }
        }
      },
      transcription: {
        bsonType: "object",
        required: ["status", "engine", "text"],
        properties: {
          status: { enum: ["pending", "completed", "failed"] },
          engine: { enum: ["faster-whisper"] },
          modelVersion: { bsonType: ["string", "null"] },
          language: { bsonType: ["string", "null"] },
          text: { bsonType: ["string", "null"] },
          confidence: { bsonType: ["int", "long", "double", "null"], minimum: 0, maximum: 1 },
          transcribedAt: { bsonType: ["date", "null"] }
        }
      },
      riskAnalysis: {
        bsonType: "object",
        required: [
          "status", "orchestrator", "model", "tierId", "tierRank",
          "rationale", "indicators", "patternEvidence", "action",
          "referenceUsage", "escalation"
        ],
        properties: {
          status: { enum: ["pending", "completed", "failed"] },
          orchestrator: { enum: ["NemoClaw"] },
          model: { enum: ["Qwen 27B"] },
          tierId: { enum: [null, "tier-1-mild", "tier-2-moderate", "tier-3-at-risk"] },
          tierRank: { enum: [null, 1, 2, 3] },
          rationale: { bsonType: ["string", "null"] },
          indicators: { bsonType: "array", items: { bsonType: "string" } },
          patternEvidence: {
            bsonType: "object",
            required: [
              "sameTriggerKey", "consecutiveCheckIns", "missedGoalTargets",
              "ambiguousResponse", "safetyRelevant", "logicalCoherenceConcern"
            ],
            properties: {
              sameTriggerKey: { bsonType: ["string", "null"] },
              consecutiveCheckIns: { bsonType: ["int", "long"], minimum: 0 },
              missedGoalTargets: { bsonType: ["int", "long"], minimum: 0 },
              ambiguousResponse: { bsonType: "bool" },
              safetyRelevant: { bsonType: "bool" },
              logicalCoherenceConcern: { bsonType: "bool" }
            }
          },
          action: {
            bsonType: "object",
            required: ["name", "gated", "gate", "status"],
            properties: {
              name: {
                enum: [
                  null,
                  "acknowledge_or_surface_reference",
                  "flag_pattern_for_clinician",
                  "escalate_to_clinician"
                ]
              },
              gated: { bsonType: "bool" },
              gate: { enum: [null, "OpenShell"] },
              status: { enum: ["pending_analysis", "awaiting_gate", "executed", "failed"] }
            }
          },
          referenceUsage: {
            bsonType: "object",
            required: [
              "surfacedPatientFacingReferenceIds", "clinicianOnlyReferenceIds",
              "upstreamProgramResourceId"
            ],
            properties: {
              surfacedPatientFacingReferenceIds: {
                bsonType: "array",
                items: {
                  enum: [
                    "ref-coping-box-breathing",
                    "ref-coping-urge-surfing",
                    "ref-psychoed-craving-curve"
                  ]
                }
              },
              clinicianOnlyReferenceIds: {
                bsonType: "array",
                items: { enum: ["ref-crisis-988", "ref-crisis-ndvh"] }
              },
              upstreamProgramResourceId: { bsonType: ["string", "null"] }
            }
          },
          escalation: {
            bsonType: "object",
            required: ["terminal", "resolved", "resolvedByClinicianId", "resolvedAt"],
            properties: {
              terminal: { bsonType: "bool" },
              resolved: { bsonType: "bool" },
              resolvedByClinicianId: { bsonType: ["string", "null"] },
              resolvedAt: { bsonType: ["date", "null"] }
            }
          },
          analyzedAt: { bsonType: ["date", "null"] }
        }
      },
      guidance: {
        bsonType: "object",
        required: ["status", "referenceLibraryVersion", "responseText"],
        properties: {
          status: { enum: ["pending", "completed", "failed"] },
          referenceLibraryVersion: { bsonType: ["string", "null"] },
          responseText: { bsonType: ["string", "null"] },
          generatedAt: { bsonType: ["date", "null"] }
        }
      },
      alert: {
        bsonType: "object",
        required: ["required", "status"],
        properties: {
          required: { bsonType: "bool" },
          status: {
            enum: [
              "pending_analysis", "not_required", "awaiting_openshell",
              "pattern_flagged", "reviewed", "escalated", "acknowledged", "resolved"
            ]
          },
          careTeamAlertedAt: { bsonType: ["date", "null"] },
          reviewedAt: { bsonType: ["date", "null"] },
          reviewedBy: { bsonType: ["string", "null"] },
          escalatedToClinicianAt: { bsonType: ["date", "null"] }
        }
      },
      responseAudio: {
        bsonType: "object",
        required: ["status", "engine", "driveUri"],
        properties: {
          status: { enum: ["pending", "rendered", "played", "failed"] },
          engine: { enum: ["Kokoro"] },
          driveUri: { bsonType: ["string", "null"] },
          renderedAt: { bsonType: ["date", "null"] },
          playedAt: { bsonType: ["date", "null"] }
        }
      },
      createdAt: { bsonType: "date" },
      updatedAt: { bsonType: "date" }
    }
  }
});

anchorDb.patients.createIndex(
  { "identifiers.system": 1, "identifiers.value": 1 },
  { unique: true, name: "uq_patient_identifier" }
);
anchorDb.careTeams.createIndex(
  { patientIds: 1 },
  { unique: true, name: "uq_patient_team_membership" }
);
anchorDb.careTeams.createIndex({ clinicianId: 1 }, { name: "idx_teams_clinician" });
anchorDb.careTeams.createIndex(
  { "identifiers.system": 1, "identifiers.value": 1 },
  { unique: true, name: "uq_care_team_identifier" }
);
anchorDb.conditions.createIndex({ patientId: 1 }, { name: "idx_conditions_patient" });
anchorDb.goals.createIndex({ patientId: 1 }, { name: "idx_goals_patient" });
anchorDb.carePlans.createIndex({ patientId: 1 }, { unique: true, name: "uq_care_plan_patient" });
anchorDb.carePlans.createIndex({ careTeamId: 1 }, { name: "idx_care_plan_team" });
anchorDb.carePlans.createIndex({ authorClinicianId: 1 }, { name: "idx_care_plan_author" });
anchorDb.healthHistories.createIndex({ patientId: 1 }, { unique: true, name: "uq_health_history_patient" });
anchorDb.healthHistories.createIndex(
  { "entries.applicableTierId": 1, "entries.status": 1 },
  { name: "idx_health_history_tier_status" }
);
anchorDb.voiceRiskTiers.createIndex({ rank: 1 }, { unique: true, name: "uq_voice_risk_tier_rank" });
anchorDb.voiceAnalyses.createIndex(
  { patientId: 1, "call.receivedAt": -1 },
  { name: "idx_voice_patient_received" }
);
anchorDb.voiceAnalyses.createIndex(
  { "riskAnalysis.tierRank": 1, "riskAnalysis.analyzedAt": -1 },
  { name: "idx_voice_risk_queue" }
);
anchorDb.voiceAnalyses.createIndex(
  { careTeamId: 1, "alert.status": 1, "call.receivedAt": -1 },
  { name: "idx_voice_care_team_alerts" }
);
anchorDb.voiceAnalyses.createIndex(
  { "inputAudio.driveUri": 1 },
  { unique: true, name: "uq_voice_input_drive_uri" }
);
