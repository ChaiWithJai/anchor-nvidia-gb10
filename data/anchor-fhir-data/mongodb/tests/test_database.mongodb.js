const anchorDb = db.getSiblingDB("anchor_fhir");
let failures = 0;

function check(condition, message) {
  if (condition) {
    print(`PASS: ${message}`);
  } else {
    failures += 1;
    print(`FAIL: ${message}`);
  }
}

function idSet(collectionName) {
  return new Set(anchorDb.getCollection(collectionName).find({}, { _id: 1 }).toArray().map(document => document._id));
}

const expectedCounts = {
  patients: 10,
  clinicians: 2,
  careTeams: 5,
  conditions: 11,
  goals: 10,
  carePlans: 10,
  voiceRiskTiers: 3,
  healthHistories: 10
};

for (const [collectionName, expectedCount] of Object.entries(expectedCounts)) {
  check(
    anchorDb.getCollection(collectionName).countDocuments({}) === expectedCount,
    `${collectionName} contains ${expectedCount} documents`
  );
}

const patientIds = idSet("patients");
const clinicianIds = idSet("clinicians");
const goalIds = idSet("goals");
const careTeamIds = idSet("careTeams");
const carePlanIds = idSet("carePlans");
const teams = anchorDb.careTeams.find({}).toArray();

const healthHistories = anchorDb.healthHistories.find({}).toArray();
check(
  healthHistories.length === 10 && new Set(healthHistories.map(history => history.patientId)).size === 10,
  "every patient has exactly one health-history document"
);
check(
  healthHistories.every(history => patientIds.has(history.patientId) && history.synthetic === true),
  "health histories reference existing patients and are marked synthetic"
);
check(
  healthHistories.every(history => history.entries.every(entry =>
    entry.applicableTierId !== "tier-2-moderate" || entry.consecutiveCheckIns >= 3
  )),
  "Tier 2 health-history entries have a qualifying recurring pattern"
);

check(
  teams.every(team => Array.isArray(team.patientIds) && team.patientIds.length === 2 && new Set(team.patientIds).size === 2),
  "every care team has exactly two unique patients"
);

const assignedPatientIds = teams.flatMap(team => team.patientIds);
check(
  assignedPatientIds.length === 10 && new Set(assignedPatientIds).size === 10,
  "the ten team assignments contain no duplicate patient"
);
check(
  [...patientIds].every(patientId => assignedPatientIds.includes(patientId)),
  "every patient belongs to a care team"
);
check(
  teams.every(team => clinicianIds.has(team.clinicianId)),
  "every care team references an existing clinician"
);

const clinicianTeamCounts = {};
for (const team of teams) {
  clinicianTeamCounts[team.clinicianId] = (clinicianTeamCounts[team.clinicianId] || 0) + 1;
}
check(
  clinicianTeamCounts["clinician-01"] === 3 && clinicianTeamCounts["clinician-02"] === 2,
  "clinicians cover three and two teams respectively"
);

for (const collectionName of ["conditions", "goals", "carePlans"]) {
  const danglingPatients = anchorDb.getCollection(collectionName)
    .countDocuments({ patientId: { $nin: [...patientIds] } });
  check(danglingPatients === 0, `${collectionName} has no dangling patient references`);
}

const carePlans = anchorDb.carePlans.find({}).toArray();
check(
  carePlans.every(plan => plan.goalIds.every(goalId => goalIds.has(goalId))),
  "care plans have no dangling goal references"
);

const goalById = new Map(anchorDb.goals.find({}).toArray().map(goal => [goal._id, goal]));
check(
  carePlans.every(plan => plan.goalIds.every(goalId => goalById.get(goalId).patientId === plan.patientId)),
  "every care plan goal belongs to the same patient"
);

const careTeamInfo = anchorDb.getCollectionInfos({ name: "careTeams" })[0];
const careTeamValidator = careTeamInfo && careTeamInfo.options && careTeamInfo.options.validator;
const patientIdsSchema = careTeamValidator && careTeamValidator.$jsonSchema.properties.patientIds;
check(
  patientIdsSchema && patientIdsSchema.minItems === 2 && patientIdsSchema.maxItems === 2 && patientIdsSchema.uniqueItems === true,
  "care team validator enforces exactly two unique patient IDs"
);

const teamIndexes = anchorDb.careTeams.getIndexes();
check(
  teamIndexes.some(index => index.name === "uq_patient_team_membership" && index.unique === true),
  "unique patient-to-team membership index exists"
);
check(
  teamIndexes.some(index => index.name === "idx_teams_clinician"),
  "clinician lookup index exists"
);

const voiceAnalysisInfo = anchorDb.getCollectionInfos({ name: "voiceAnalyses" })[0];
check(Boolean(voiceAnalysisInfo), "voiceAnalyses collection exists");

if (voiceAnalysisInfo) {
  const voiceSchema = voiceAnalysisInfo.options.validator.$jsonSchema;
  check(
    voiceSchema.properties.riskAnalysis.properties.tierId.enum.join(",") ===
      ",tier-1-mild,tier-2-moderate,tier-3-at-risk",
    "voice risk is constrained to the locked three-tier model"
  );

  const voiceDocuments = anchorDb.voiceAnalyses.find({}).toArray();
  check(
    voiceDocuments.every(document => patientIds.has(document.patientId)),
    "voice analyses have no dangling patient references"
  );
  check(
    voiceDocuments.every(document => careTeamIds.has(document.careTeamId)),
    "voice analyses have no dangling care-team references"
  );
  check(
    voiceDocuments.every(document => carePlanIds.has(document.carePlanId)),
    "voice analyses have no dangling care-plan references"
  );
  check(
    voiceDocuments.every(document => {
      const risk = document.riskAnalysis;
      if (risk.tierId === "tier-1-mild") {
        return risk.action.gated === false && document.alert.required === false;
      }
      if (risk.tierId === "tier-2-moderate") {
        return risk.action.name === "flag_pattern_for_clinician" &&
          risk.action.gated === true && risk.action.gate === "OpenShell" &&
          document.alert.required === true;
      }
      if (risk.tierId === "tier-3-at-risk") {
        return risk.action.name === "escalate_to_clinician" &&
          risk.action.gated === false && risk.escalation.terminal === true &&
          document.alert.required === true;
      }
      return risk.status === "pending" && risk.tierId === null;
    }),
    "stored voice analyses obey tier action, gate, alert, and terminal-escalation rules"
  );

  const voiceIndexes = anchorDb.voiceAnalyses.getIndexes();
  for (const indexName of [
    "idx_voice_patient_received",
    "idx_voice_risk_queue",
    "idx_voice_care_team_alerts",
    "uq_voice_input_drive_uri"
  ]) {
    check(voiceIndexes.some(index => index.name === indexName), `${indexName} exists`);
  }
}

if (failures > 0) {
  print(`\n${failures} MongoDB integration test(s) failed.`);
  quit(1);
}

print("\nAll MongoDB integration tests passed.");
