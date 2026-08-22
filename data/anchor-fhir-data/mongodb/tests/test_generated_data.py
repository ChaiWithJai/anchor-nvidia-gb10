#!/usr/bin/env python3
"""Offline tests for the generated MongoDB collection documents."""

from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path


MONGODB_DIR = Path(__file__).resolve().parents[1]
COLLECTION_DIR = MONGODB_DIR / "collections"


def load_collection(name: str) -> list[dict]:
    with (COLLECTION_DIR / f"{name}.json").open(encoding="utf-8") as source:
        return json.load(source)


class MongoGeneratedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.patients = load_collection("patients")
        cls.clinicians = load_collection("clinicians")
        cls.care_teams = load_collection("careTeams")
        cls.conditions = load_collection("conditions")
        cls.goals = load_collection("goals")
        cls.care_plans = load_collection("carePlans")
        cls.voice_risk_tiers = load_collection("voiceRiskTiers")
        cls.health_histories = load_collection("healthHistories")

        cls.patient_ids = {document["_id"] for document in cls.patients}
        cls.clinician_ids = {document["_id"] for document in cls.clinicians}
        cls.goal_by_id = {document["_id"]: document for document in cls.goals}

    def test_expected_collection_counts(self) -> None:
        self.assertEqual(len(self.patients), 10)
        self.assertEqual(len(self.clinicians), 2)
        self.assertEqual(len(self.care_teams), 5)
        self.assertEqual(len(self.conditions), 11)
        self.assertEqual(len(self.goals), 10)
        self.assertEqual(len(self.care_plans), 10)
        self.assertEqual(len(self.voice_risk_tiers), 3)
        self.assertEqual(len(self.health_histories), 10)

    def test_document_ids_are_unique_per_collection(self) -> None:
        for collection in (
            self.patients,
            self.clinicians,
            self.care_teams,
            self.conditions,
            self.goals,
            self.care_plans,
            self.voice_risk_tiers,
            self.health_histories,
        ):
            ids = [document["_id"] for document in collection]
            self.assertEqual(len(ids), len(set(ids)))

    def test_every_team_has_two_unique_patients(self) -> None:
        for team in self.care_teams:
            self.assertEqual(len(team["patientIds"]), 2, team["_id"])
            self.assertEqual(len(set(team["patientIds"])), 2, team["_id"])
            self.assertTrue(set(team["patientIds"]).issubset(self.patient_ids))
            self.assertEqual(len(team["patientCareTeamIds"]), 2, team["_id"])
            self.assertEqual(len(set(team["patientCareTeamIds"])), 2, team["_id"])
            self.assertRegex(team["sourceGroupId"], r"^patient-group-[0-9]{2}$")

    def test_every_patient_belongs_to_exactly_one_team(self) -> None:
        assignments = [patient_id for team in self.care_teams for patient_id in team["patientIds"]]
        self.assertEqual(set(assignments), self.patient_ids)
        self.assertTrue(all(count == 1 for count in Counter(assignments).values()))

    def test_every_team_has_one_valid_clinician(self) -> None:
        for team in self.care_teams:
            self.assertIn(team["clinicianId"], self.clinician_ids)
            self.assertIsInstance(team["clinicianRole"], str)
            self.assertTrue(team["clinicianRole"])

    def test_clinician_to_team_distribution(self) -> None:
        assignment_counts = Counter(team["clinicianId"] for team in self.care_teams)
        self.assertEqual(assignment_counts, Counter({"clinician-01": 3, "clinician-02": 2}))

    def test_clinical_documents_reference_existing_patients(self) -> None:
        for collection in (self.conditions, self.goals, self.care_plans):
            for document in collection:
                self.assertIn(document["patientId"], self.patient_ids, document["_id"])

    def test_care_plan_goals_exist_and_belong_to_same_patient(self) -> None:
        for care_plan in self.care_plans:
            self.assertGreaterEqual(len(care_plan["goalIds"]), 1)
            for goal_id in care_plan["goalIds"]:
                self.assertIn(goal_id, self.goal_by_id, care_plan["_id"])
                self.assertEqual(
                    self.goal_by_id[goal_id]["patientId"],
                    care_plan["patientId"],
                    care_plan["_id"],
                )

    def test_patient_identifiers_are_unique(self) -> None:
        identifiers = []
        for patient in self.patients:
            for identifier in patient["identifiers"]:
                identifiers.append((identifier.get("system"), identifier.get("value")))
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_patients_have_realistic_synthetic_profiles(self) -> None:
        for patient in self.patients:
            self.assertNotEqual(patient["addresses"][0]["city"], "Demo City")
            self.assertRegex(patient["addresses"][0]["postalCode"], r"^[0-9]{5}$")
            self.assertGreaterEqual(len(patient["telecom"]), 2)
            phone = next(item["value"] for item in patient["telecom"] if item["system"] == "phone")
            email = next(item["value"] for item in patient["telecom"] if item["system"] == "email")
            self.assertIn("555", phone)
            self.assertTrue(email.endswith("@example.com"))
            self.assertTrue(patient["maritalStatus"].get("text"))
            self.assertTrue(patient["employmentStatus"])
            self.assertFalse(patient["names"][0]["family"].endswith("."))

    def test_care_teams_have_operational_details(self) -> None:
        for team in self.care_teams:
            self.assertGreaterEqual(len(team["identifiers"]), 1)
            self.assertGreaterEqual(len(team["categories"]), 1)
            self.assertGreaterEqual(len(team["telecom"]), 1)
            self.assertIn("start", team["period"])
            self.assertTrue(any(note.startswith("Coverage hours:") for note in team["notes"]))

    def test_care_plans_have_valid_ownership_and_schedule(self) -> None:
        team_ids = {team["_id"] for team in self.care_teams}
        clinician_ids = {clinician["_id"] for clinician in self.clinicians}
        condition_ids = {condition["_id"] for condition in self.conditions}
        for plan in self.care_plans:
            self.assertIn(plan["careTeamId"], team_ids)
            team = next(item for item in self.care_teams if item["_id"] == plan["careTeamId"])
            self.assertIn(plan["patientCareTeamId"], team["patientCareTeamIds"])
            self.assertIn(plan["authorClinicianId"], clinician_ids)
            self.assertTrue(set(plan["conditionIds"]).issubset(condition_ids))
            self.assertTrue(plan["title"].startswith("Personalized recovery plan for "))
            self.assertNotIn(plan["patientId"], plan["title"])
            self.assertTrue(all(activity["status"] == "scheduled" for activity in plan["activities"]))
            self.assertTrue(all(activity["schedule"] for activity in plan["activities"]))

    def test_voice_risk_tier_actions_and_gates(self) -> None:
        tiers = {tier["_id"]: tier for tier in self.voice_risk_tiers}
        self.assertEqual(
            tiers["tier-1-mild"]["action"],
            {"name": "acknowledge_or_surface_reference", "gated": False, "gate": None},
        )
        self.assertEqual(tiers["tier-2-moderate"]["action"]["name"], "flag_pattern_for_clinician")
        self.assertTrue(tiers["tier-2-moderate"]["action"]["gated"])
        self.assertEqual(tiers["tier-2-moderate"]["action"]["gate"], "OpenShell")
        self.assertEqual(tiers["tier-3-at-risk"]["action"]["name"], "escalate_to_clinician")
        self.assertFalse(tiers["tier-3-at-risk"]["action"]["gated"])
        self.assertTrue(tiers["tier-3-at-risk"]["action"]["alwaysOpen"])
        self.assertTrue(tiers["tier-3-at-risk"]["terminal"])

    def test_voice_reference_library_boundaries(self) -> None:
        tiers = {tier["_id"]: tier for tier in self.voice_risk_tiers}
        allowed_patient_facing = {
            "ref-coping-box-breathing",
            "ref-coping-urge-surfing",
            "ref-psychoed-craving-curve",
        }
        for tier_id in ("tier-1-mild", "tier-2-moderate"):
            self.assertEqual(set(tiers[tier_id]["eligiblePatientFacingReferenceIds"]), allowed_patient_facing)
            self.assertEqual(tiers[tier_id]["clinicianOnlyReferenceIds"], [])
        self.assertEqual(tiers["tier-3-at-risk"]["eligiblePatientFacingReferenceIds"], [])
        self.assertEqual(
            set(tiers["tier-3-at-risk"]["clinicianOnlyReferenceIds"]),
            {"ref-crisis-988", "ref-crisis-ndvh"},
        )

    def test_every_patient_has_one_synthetic_health_history(self) -> None:
        history_patient_ids = [history["patientId"] for history in self.health_histories]
        self.assertEqual(set(history_patient_ids), self.patient_ids)
        self.assertEqual(len(history_patient_ids), len(set(history_patient_ids)))
        for history in self.health_histories:
            self.assertTrue(history["synthetic"])
            self.assertGreaterEqual(len(history["entries"]), 1)

    def test_health_history_references_and_tier_rules(self) -> None:
        condition_ids = {condition["_id"] for condition in self.conditions}
        goal_ids = set(self.goal_by_id)
        tier_ids = {tier["_id"] for tier in self.voice_risk_tiers}
        for history in self.health_histories:
            for entry in history["entries"]:
                self.assertTrue(set(entry["relatedConditionIds"]).issubset(condition_ids))
                self.assertTrue(set(entry["relatedGoalIds"]).issubset(goal_ids))
                self.assertIn(entry["applicableTierId"], tier_ids)
                if entry["applicableTierId"] == "tier-2-moderate":
                    self.assertGreaterEqual(entry["consecutiveCheckIns"], 3)

    def test_health_history_contains_no_fabricated_tier_three_event(self) -> None:
        tiers = {
            entry["applicableTierId"]
            for history in self.health_histories
            for entry in history["entries"]
        }
        self.assertNotIn("tier-3-at-risk", tiers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
