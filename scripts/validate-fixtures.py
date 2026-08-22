#!/usr/bin/env python3
"""Static validation for Anchor's deterministic synthetic roster."""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from careline import fixtures  # noqa: E402


def main() -> int:
    anchor = fixtures.dataset_anchor()
    patients = fixtures.build_patients(anchor)
    fixtures.validate_population(patients)
    assert len({fixtures.plan_for(patient, index)["plan_id"] for index, patient in enumerate(patients)}) == 30
    assert len({fixtures.goal_for(patient, index)["goal_id"] for index, patient in enumerate(patients)}) == 30
    assert all(patient["care_team_id"] == fixtures.CARE_TEAM_ID for patient in patients)
    assert all(patient["synthetic_demo_data"] for patient in patients)
    assert sorted({patient["risk_priority"] for patient in patients}) == [1, 2, 3, 4]
    with open(
        os.path.join(ROOT, "app", "careline", "bh-reference-library.seed.json"),
        encoding="utf-8",
    ) as source:
        references = json.load(source)
    ids = [item["reference_id"] for item in references["references"]]
    assert len(ids) == len(set(ids)) == 5
    print(
        f"PASS {fixtures.DATASET_VERSION}: 30 patients, "
        f"{len(ids)} reviewed references, all queue tiers and voice modes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
