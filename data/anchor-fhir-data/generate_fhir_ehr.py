#!/usr/bin/env python3
"""
generate_fhir_ehr.py

Builds 10 synthetic, FHIR R4-valid EHR record bundles for behavioral-health
patients with a documented substance use disorder (SUD) diagnosis and linked
CarePlan/Goal resources. Five operational Groups pair two patients per team;
each patient has a patient-scoped CareTeam and the five operational teams are
covered by two clinicians. This is a PARALLEL dataset to Anchor's own
app-specific Recovery Plan / Behavioral Health Reference Library data store
(see anchor-data-stores/) — it represents the clinical-EHR side a real FHIR
integration would eventually read from, not something wired into the live
demo build.

Every value here is synthetic. No real patient, provider, or contact
information appears anywhere in this file or its output.

Coding notes (see README.md for the full rationale):
- Diagnoses use ICD-10-CM only (system http://hl7.org/fhir/sid/icd-10-cm).
  SNOMED CT codes are deliberately omitted rather than guessed — a numeric
  SNOMED concept ID that's wrong looks identical to one that's right, and
  this project's own rule (never invent a source/code) applies here too.
- DSM-5 severity maps to ICD-10-CM's two-tier abuse/dependence split per
  standard coding guidance: mild -> abuse code (x.1x), moderate/severe ->
  dependence code (x.2x). "Polysubstance" is expressed as multiple Condition
  resources (one per substance), matching current ICD-10-CM/DSM-5 practice
  rather than a single invented "polysubstance" code.
"""

import json
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

ICD10_ALCOHOL_ABUSE = ("F10.10", "Alcohol abuse, uncomplicated")
ICD10_ALCOHOL_DEPENDENCE = ("F10.20", "Alcohol dependence, uncomplicated")
ICD10_OPIOID_ABUSE = ("F11.10", "Opioid abuse, uncomplicated")
ICD10_OPIOID_DEPENDENCE = ("F11.20", "Opioid dependence, uncomplicated")
ICD10_CANNABIS_ABUSE = ("F12.10", "Cannabis abuse, uncomplicated")
ICD10_CANNABIS_DEPENDENCE = ("F12.20", "Cannabis dependence, uncomplicated")
ICD10_COCAINE_ABUSE = ("F14.10", "Cocaine abuse, uncomplicated")
ICD10_COCAINE_DEPENDENCE = ("F14.20", "Cocaine dependence, uncomplicated")
ICD10_STIMULANT_ABUSE = ("F15.10", "Other stimulant abuse, uncomplicated")
ICD10_STIMULANT_DEPENDENCE = ("F15.20", "Other stimulant dependence, uncomplicated")

ICD10_SYSTEM = "http://hl7.org/fhir/sid/icd-10-cm"

CLINICIANS = [
    {
        "id": "clinician-01",
        "given": "Maya",
        "family": "Chen",
        "display": "Dr. Maya Chen (seeded/fictional)",
        "email": "maya.chen@anchor-demo.example.com",
        "phone": "+1-212-555-0101",
        "license": "SYN-NY-MD-1001",
        "qualification": "Addiction medicine physician",
    },
    {
        "id": "clinician-02",
        "given": "Liam",
        "family": "Patel",
        "display": "Dr. Liam Patel (seeded/fictional)",
        "email": "liam.patel@anchor-demo.example.com",
        "phone": "+1-212-555-0102",
        "license": "SYN-NY-MD-1002",
        "qualification": "Addiction medicine physician",
    },
]

PATIENT_PROFILES = [
    dict(given="Jordan", family="Mercer", gender="male", line="214 Cedar Walk", city="Brooklyn", state="NY", postal_code="11215", phone="+1-917-555-0101", email="jordan.mercer@example.com", language="en", marital_code="S", marital_text="Never Married", employment_status="employed_full_time"),
    dict(given="Casey", family="Bennett", gender="female", line="88 Juniper Avenue", city="Queens", state="NY", postal_code="11373", phone="+1-917-555-0102", email="casey.bennett@example.com", language="en", marital_code="S", marital_text="Never Married", employment_status="employed_part_time"),
    dict(given="Riley", family="Carter", gender="other", line="31 Grove Terrace", city="Jersey City", state="NJ", postal_code="07302", phone="+1-201-555-0103", email="riley.carter@example.com", language="en", marital_code="S", marital_text="Never Married", employment_status="employed_full_time"),
    dict(given="Morgan", family="Diaz", gender="male", line="407 Market Lane", city="Newark", state="NJ", postal_code="07103", phone="+1-973-555-0104", email="morgan.diaz@example.com", language="en", marital_code="D", marital_text="Divorced", employment_status="unemployed"),
    dict(given="Avery", family="Ellis", gender="female", line="62 Parkview Road", city="Yonkers", state="NY", postal_code="10701", phone="+1-914-555-0105", email="avery.ellis@example.com", language="en", marital_code="D", marital_text="Divorced", employment_status="employed_part_time"),
    dict(given="Quinn", family="Foster", gender="male", line="119 Willow Street", city="Paterson", state="NJ", postal_code="07501", phone="+1-973-555-0106", email="quinn.foster@example.com", language="en", marital_code="M", marital_text="Married", employment_status="employed_full_time"),
    dict(given="Sage", family="Green", gender="other", line="53 Chapel Court", city="New Haven", state="CT", postal_code="06510", phone="+1-203-555-0107", email="sage.green@example.com", language="en", marital_code="S", marital_text="Never Married", employment_status="student_part_time"),
    dict(given="Drew", family="Hayes", gender="male", line="275 Harbor Drive", city="Stamford", state="CT", postal_code="06901", phone="+1-203-555-0108", email="drew.hayes@example.com", language="en", marital_code="M", marital_text="Married", employment_status="employed_full_time"),
    dict(given="Reese", family="Irving", gender="female", line="146 Belmont Avenue", city="Bronx", state="NY", postal_code="10458", phone="+1-718-555-0109", email="reese.irving@example.com", language="en", marital_code="S", marital_text="Never Married", employment_status="employed_full_time"),
    dict(given="Cameron", family="James", gender="male", line="90 Maple Crescent", city="White Plains", state="NY", postal_code="10601", phone="+1-914-555-0110", email="cameron.james@example.com", language="en", marital_code="L", marital_text="Legally Separated", employment_status="employed_part_time"),
]

CARE_TEAM_PROFILES = [
    dict(name="Harbor Recovery Team", phone="+1-212-555-0201", hours="Mon-Fri 08:00-18:00", start="2026-01-01"),
    dict(name="Northstar Recovery Team", phone="+1-212-555-0202", hours="Mon-Fri 09:00-19:00", start="2026-01-01"),
    dict(name="Bridgeway Recovery Team", phone="+1-212-555-0203", hours="Mon-Sat 08:00-17:00", start="2026-02-01"),
    dict(name="Horizon Recovery Team", phone="+1-212-555-0204", hours="Mon-Fri 08:00-20:00", start="2026-02-01"),
    dict(name="Pathfinder Recovery Team", phone="+1-212-555-0205", hours="Mon-Sat 09:00-18:00", start="2026-03-01"),
]


def condition_code(code_tuple):
    code, display = code_tuple
    return {
        "coding": [{"system": ICD10_SYSTEM, "code": code, "display": display}],
        "text": display,
    }


def make_patient(pid, identifier_value, profile, birth_date):
    return {
        "resourceType": "Patient",
        "id": pid,
        "identifier": [
            {
                "system": "urn:anchor:demo-mrn",
                "value": identifier_value,
            }
        ],
        "name": [
            {
                "use": "official",
                "given": [profile["given"]],
                "family": profile["family"],
                "text": f"{profile['given']} {profile['family']}",
            }
        ],
        "telecom": [
            {"system": "phone", "value": profile["phone"], "use": "mobile"},
            {"system": "email", "value": profile["email"], "use": "home"},
        ],
        "gender": profile["gender"],
        "birthDate": birth_date,
        "address": [
            {
                "use": "home",
                "type": "physical",
                "text": f"{profile['line']}, {profile['city']}, {profile['state']} {profile['postal_code']}",
                "line": [profile["line"]],
                "city": profile["city"],
                "state": profile["state"],
                "postalCode": profile["postal_code"],
                "country": "US",
            }
        ],
        "maritalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                    "code": profile["marital_code"],
                    "display": profile["marital_text"],
                }
            ],
            "text": profile["marital_text"],
        },
        "communication": [
            {
                "language": {
                    "coding": [{"system": "urn:ietf:bcp:47", "code": profile["language"], "display": "English"}],
                    "text": "English",
                },
                "preferred": True,
            }
        ],
        "extension": [
            {
                "url": "urn:anchor:employment-status",
                "valueCode": profile["employment_status"],
            }
        ],
        "meta": {"tag": [{"system": "urn:anchor:demo-data", "code": "synthetic"}]},
    }


def make_condition(cid, patient_id, code_tuple, onset_date, severity_note):
    return {
        "resourceType": "Condition",
        "id": cid,
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "problem-list-item",
                    }
                ]
            }
        ],
        "code": condition_code(code_tuple),
        "subject": {"reference": f"Patient/{patient_id}"},
        "onsetDateTime": onset_date,
        "note": [{"text": severity_note}],
    }


def make_goal(gid, patient_id, description, due_date, measure_text):
    return {
        "resourceType": "Goal",
        "id": gid,
        "lifecycleStatus": "active",
        "description": {"text": description},
        "subject": {"reference": f"Patient/{patient_id}"},
        "target": [{"measure": {"text": measure_text}, "dueDate": due_date}],
    }


def make_care_plan(
    cpid,
    patient_id,
    patient_display_name,
    goal_ids,
    condition_ids,
    team_id,
    clinician,
    period_start,
    period_end,
    activities,
    category_text,
):
    return {
        "resourceType": "CarePlan",
        "id": cpid,
        "identifier": [{"system": "urn:anchor:demo-care-plan", "value": f"ACP-{cpid[-2:]}-2026"}],
        "title": f"Personalized recovery plan for {patient_display_name}",
        "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
        "status": "active",
        "intent": "plan",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
                        "code": "assess-plan",
                    }
                ],
                "text": category_text,
            }
        ],
        "subject": {"reference": f"Patient/{patient_id}"},
        "created": period_start,
        "author": {"reference": f"Practitioner/{clinician['id']}", "display": clinician["display"]},
        "careTeam": [{"reference": f"CareTeam/{team_id}"}],
        "addresses": [{"reference": f"Condition/{condition_id}"} for condition_id in condition_ids],
        "period": {"start": period_start, "end": period_end},
        "goal": [{"reference": f"Goal/{g}"} for g in goal_ids],
        "activity": [
            {
                "detail": {
                    "status": "scheduled",
                    "description": activity,
                    "scheduledString": "Per individualized recovery schedule",
                }
            }
            for activity in activities
        ],
        "note": [
            {
                "text": "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
            }
        ],
    }


def make_practitioner(clinician):
    return {
        "resourceType": "Practitioner",
        "id": clinician["id"],
        "name": [
            {
                "use": "official",
                "given": [clinician["given"]],
                "family": clinician["family"],
                "text": clinician["display"],
            }
        ],
        "identifier": [
            {
                "system": "urn:anchor:synthetic-clinician-license",
                "value": clinician["license"],
            }
        ],
        "telecom": [
            {"system": "phone", "value": clinician["phone"], "use": "work"},
            {"system": "email", "value": clinician["email"], "use": "work"},
        ],
        "qualification": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "urn:anchor:synthetic-qualification",
                            "code": "addiction-medicine",
                            "display": clinician["qualification"],
                        }
                    ],
                    "text": clinician["qualification"],
                }
            }
        ],
        "meta": {"tag": [{"system": "urn:anchor:demo-data", "code": "synthetic"}]},
    }


def make_patient_group(group_id, patient_ids, team_number, profile):
    return {
        "resourceType": "Group",
        "id": group_id,
        "identifier": [
            {
                "system": "urn:anchor:operational-care-team",
                "value": f"ACT-{team_number:02d}",
            }
        ],
        "type": "person",
        "actual": True,
        "name": f"{profile['name']} patient cohort",
        "quantity": len(patient_ids),
        "member": [{"entity": {"reference": f"Patient/{patient_id}"}} for patient_id in patient_ids],
    }


def make_care_team(ctid, patient_id, team_number, clinician, clinician_role, profile):
    return {
        "resourceType": "CareTeam",
        "id": ctid,
        "identifier": [
            {"system": "urn:anchor:demo-patient-care-team", "value": f"PCT-{patient_id[-2:]}"},
            {"system": "urn:anchor:operational-care-team", "value": f"ACT-{team_number:02d}"},
        ],
        "status": "active",
        "name": f"{profile['name']} — {patient_id}",
        "category": [{"text": "Behavioral health recovery management"}],
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {"start": profile["start"]},
        "telecom": [{"system": "phone", "value": profile["phone"], "use": "work"}],
        "participant": [
            {
                "role": [{"text": clinician_role}],
                "member": {
                    "reference": f"Practitioner/{clinician['id']}",
                    "display": clinician["display"],
                },
                "period": {"start": profile["start"]},
            }
        ],
        "note": [
            {"text": f"Coverage hours: {profile['hours']}."},
            {
                "text": (
                    "Anchor (voice check-in agent) is NOT a CareTeam member and is not "
                    "represented here. It is a patient-facing adherence/check-in tool that "
                    "reads this record's CarePlan and Goal resources — it never makes a "
                    "clinical judgment, diagnosis, or care decision on this team's behalf."
                )
            }
        ],
    }


def build_bundle(patient, condition, goals, care_plan, care_team):
    entries = [patient, condition] + goals + [care_plan, care_team]
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": r} for r in entries],
    }


def patient_def(i):
    """Returns (patient_kwargs, [ (condition_code, onset, severity_note) ], goal_defs, activities, category_text, clinician)."""

    defs = [
        # 1 — alcohol, moderate, outpatient, self-referred
        dict(
            identifier="demo-patient-01",
            given="Jordan",
            family="A.",
            gender="unknown",
            birth_date="1988-03-14",
            city="Demo City",
            state="ST",
            conditions=[(ICD10_ALCOHOL_DEPENDENCE, "2026-05-01", "DSM-5 moderate alcohol use disorder")],
            goals=[("Reduce drinking days to zero across a 30-day window", "2026-09-20", "self-reported drinking days/week")],
            activities=["Daily sobriety check-in via Anchor voice agent", "Weekly outpatient counseling session"],
            category_text="Substance use disorder treatment plan",
            clinician="Dr. R. Whitfield (seeded/fictional)",
            role="Addiction medicine physician",
        ),
        # 2 — opioid, severe, IOP, self-referred
        dict(
            identifier="demo-patient-02",
            given="Casey",
            family="B.",
            gender="unknown",
            birth_date="1992-07-22",
            city="Demo City",
            state="ST",
            conditions=[(ICD10_OPIOID_DEPENDENCE, "2026-04-10", "DSM-5 severe opioid use disorder")],
            goals=[("Complete intensive outpatient (IOP) program without unplanned discharge", "2026-10-01", "IOP session attendance rate")],
            activities=["Daily sobriety check-in via Anchor voice agent", "IOP attendance 3x/week", "Medication-assisted treatment follow-up with prescribing clinician"],
            category_text="Substance use disorder treatment plan",
            clinician="Dr. M. Alvarez (seeded/fictional)",
            role="Addiction medicine physician",
        ),
        # 3 — cocaine, mild, outpatient, self-referred
        dict(
            identifier="demo-patient-03",
            given="Riley",
            family="C.",
            gender="unknown",
            birth_date="1995-11-02",
            city="Demo City",
            state="ST",
            conditions=[(ICD10_COCAINE_ABUSE, "2026-06-05", "DSM-5 mild stimulant (cocaine) use disorder")],
            goals=[("Identify and log craving triggers for 4 consecutive weeks", "2026-09-05", "trigger log entries/week")],
            activities=["Daily sobriety check-in via Anchor voice agent", "Biweekly outpatient counseling session"],
            category_text="Substance use disorder treatment plan",
            clinician="L. Nguyen, LCSW (seeded/fictional)",
            role="Licensed clinical social worker",
        ),
        # 4 — polysubstance (alcohol + opioid), severe, IOP, court-referred
        dict(
            identifier="demo-patient-04",
            given="Morgan",
            family="D.",
            gender="unknown",
            birth_date="1985-01-30",
            city="Demo City",
            state="ST",
            conditions=[
                (ICD10_ALCOHOL_DEPENDENCE, "2026-03-18", "DSM-5 severe alcohol use disorder"),
                (ICD10_OPIOID_DEPENDENCE, "2026-03-18", "DSM-5 severe opioid use disorder — co-occurring, coded separately per current ICD-10-CM/DSM-5 guidance rather than a single 'polysubstance' code"),
            ],
            goals=[("Complete IOP program with no positive screens", "2026-11-01", "screening result per session")],
            activities=["Daily sobriety check-in via Anchor voice agent", "IOP attendance 3x/week", "Court-mandated progress reporting"],
            category_text="Substance use disorder treatment plan (court-referred)",
            clinician="Dr. R. Whitfield (seeded/fictional)",
            role="Addiction medicine physician",
        ),
        # 5 — alcohol, severe, IOP, court-referred
        dict(
            identifier="demo-patient-05",
            given="Avery",
            family="E.",
            gender="unknown",
            birth_date="1979-09-09",
            city="Demo City",
            state="ST",
            conditions=[(ICD10_ALCOHOL_DEPENDENCE, "2026-02-27", "DSM-5 severe alcohol use disorder")],
            goals=[("Maintain abstinence through court review date", "2026-12-15", "self-reported drinking days + screening result")],
            activities=["Daily sobriety check-in via Anchor voice agent", "IOP attendance 3x/week", "Court-mandated progress reporting"],
            category_text="Substance use disorder treatment plan (court-referred)",
            clinician="Dr. M. Alvarez (seeded/fictional)",
            role="Addiction medicine physician",
        ),
        # 6 — opioid, moderate, outpatient, self-referred
        dict(
            identifier="demo-patient-06",
            given="Quinn",
            family="F.",
            gender="unknown",
            birth_date="1990-05-17",
            city="Demo City",
            state="ST",
            conditions=[(ICD10_OPIOID_DEPENDENCE, "2026-05-22", "DSM-5 moderate opioid use disorder")],
            goals=[("Attend every scheduled outpatient session for 8 weeks", "2026-09-30", "session attendance rate")],
            activities=["Daily sobriety check-in via Anchor voice agent", "Weekly outpatient counseling session"],
            category_text="Substance use disorder treatment plan",
            clinician="L. Nguyen, LCSW (seeded/fictional)",
            role="Licensed clinical social worker",
        ),
        # 7 — cannabis, mild, outpatient, self-referred
        dict(
            identifier="demo-patient-07",
            given="Sage",
            family="G.",
            gender="unknown",
            birth_date="1999-12-01",
            city="Demo City",
            state="ST",
            conditions=[(ICD10_CANNABIS_ABUSE, "2026-06-30", "DSM-5 mild cannabis use disorder")],
            goals=[("Reduce use frequency to zero across a 4-week window", "2026-08-30", "self-reported use days/week")],
            activities=["Daily sobriety check-in via Anchor voice agent", "Biweekly outpatient counseling session"],
            category_text="Substance use disorder treatment plan",
            clinician="L. Nguyen, LCSW (seeded/fictional)",
            role="Licensed clinical social worker",
        ),
        # 8 — stimulant (methamphetamine), moderate, outpatient, self-referred
        dict(
            identifier="demo-patient-08",
            given="Drew",
            family="H.",
            gender="unknown",
            birth_date="1983-08-08",
            city="Demo City",
            state="ST",
            conditions=[(ICD10_STIMULANT_DEPENDENCE, "2026-04-14", "DSM-5 moderate stimulant use disorder")],
            goals=[("Sustain abstinence with negative screens for 60 days", "2026-11-14", "screening result per session")],
            activities=["Daily sobriety check-in via Anchor voice agent", "Weekly outpatient counseling session"],
            category_text="Substance use disorder treatment plan",
            clinician="Dr. R. Whitfield (seeded/fictional)",
            role="Addiction medicine physician",
        ),
        # 9 — alcohol, mild, outpatient, self-referred
        dict(
            identifier="demo-patient-09",
            given="Reese",
            family="I.",
            gender="unknown",
            birth_date="1997-02-19",
            city="Demo City",
            state="ST",
            conditions=[(ICD10_ALCOHOL_ABUSE, "2026-07-01", "DSM-5 mild alcohol use disorder")],
            goals=[("Limit drinking to zero on weeknights for 6 weeks", "2026-09-01", "self-reported drinking days/week")],
            activities=["Daily sobriety check-in via Anchor voice agent", "Biweekly outpatient counseling session"],
            category_text="Substance use disorder treatment plan",
            clinician="L. Nguyen, LCSW (seeded/fictional)",
            role="Licensed clinical social worker",
        ),
        # 10 — the post-disclosure bridge scenario, crosswalked to plan-demo-bridge
        dict(
            identifier="demo-patient-bridge",
            given="Bridge-Scenario",
            family="J.",
            gender="unknown",
            birth_date="1986-10-23",
            city="Demo City",
            state="ST",
            conditions=[(ICD10_ALCOHOL_DEPENDENCE, "2026-08-10", "DSM-5 moderate alcohol use disorder — co-occurring referral to combined accountability + substance-treatment program")],
            goals=[("Maintain abstinence through the wait for program intake", "2026-09-02", "self-reported drinking days + daily check-in engagement")],
            activities=[
                "Daily sobriety check-in via Anchor voice agent (bridge period only — does not replace the program)",
                "Scheduled intake at Riverside Accountability & Recovery Program (seeded/fictional) — combined BIP + substance treatment, self-referral accepted",
                "Any risk-shaped disclosure during a check-in routes to escalate_to_clinician() immediately — Anchor never assesses or acts on this itself",
            ],
            category_text="Substance use disorder treatment plan — post-disclosure bridge to accountability program",
            clinician="Dr. M. Alvarez (seeded/fictional)",
            role="Addiction medicine physician",
        ),
    ]
    return defs[i]


def main():
    written = []
    for i in range(10):
        d = patient_def(i)
        n = f"{i+1:02d}"
        patient_id = f"patient-{n}"
        profile = PATIENT_PROFILES[i]
        team_number = i // 2 + 1
        team_id = f"careteam-patient-{n}"
        clinician = CLINICIANS[0] if team_number <= 3 else CLINICIANS[1]

        patient = make_patient(
            patient_id, d["identifier"], profile, d["birth_date"]
        )

        conditions = []
        for j, (code_tuple, onset, note) in enumerate(d["conditions"]):
            cid = f"condition-{n}" if j == 0 else f"condition-{n}b"
            conditions.append(make_condition(cid, patient_id, code_tuple, onset, note))

        goals = []
        goal_ids = []
        for j, (desc, due, measure) in enumerate(d["goals"]):
            gid = f"goal-{n}" if j == 0 else f"goal-{n}-{j}"
            goal_ids.append(gid)
            goals.append(make_goal(gid, patient_id, desc, due, measure))

        care_plan = make_care_plan(
            f"careplan-{n}",
            patient_id,
            f"{profile['given']} {profile['family']}",
            goal_ids,
            [condition["id"] for condition in conditions],
            team_id,
            clinician,
            d["conditions"][0][1],
            max(goal[1] for goal in d["goals"]),
            d["activities"],
            d["category_text"],
        )
        patient_care_team = make_care_team(
            team_id,
            patient_id,
            team_number,
            clinician,
            "Addiction medicine physician",
            CARE_TEAM_PROFILES[team_number - 1],
        )
        # The CareTeam is patient-scoped for US Core compatibility. The shared
        # operational cohort is represented by a Group in bundle-care-teams.json.
        entries = [patient] + conditions + goals + [care_plan, patient_care_team]
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": r} for r in entries],
        }

        out_path = os.path.join(OUT_DIR, f"bundle-patient-{n}.json")
        with open(out_path, "w") as f:
            json.dump(bundle, f, indent=2)
        written.append(out_path)

    team_resources = [make_practitioner(clinician) for clinician in CLINICIANS]
    for index in range(5):
        team_number = index + 1
        number = f"{team_number:02d}"
        patient_ids = [f"patient-{2 * index + 1:02d}", f"patient-{2 * index + 2:02d}"]
        group_id = f"patient-group-{number}"
        clinician = CLINICIANS[0] if index < 3 else CLINICIANS[1]
        team_resources.append(
            make_patient_group(
                group_id,
                patient_ids,
                team_number,
                CARE_TEAM_PROFILES[index],
            )
        )

    team_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": resource} for resource in team_resources],
    }
    team_path = os.path.join(OUT_DIR, "bundle-care-teams.json")
    with open(team_path, "w") as f:
        json.dump(team_bundle, f, indent=2)
    written.append(team_path)

    return written


def validate(paths):
    """Check global references and the requested team cardinalities."""
    errors = []
    resources = {}
    for path in paths:
        with open(path) as f:
            bundle = json.load(f)
        for entry in bundle["entry"]:
            resource = entry["resource"]
            key = resource["resourceType"] + "/" + resource["id"]
            if key in resources:
                errors.append(f"duplicate resource {key}")
            resources[key] = resource

    expected_counts = {"Patient": 10, "CareTeam": 10, "Practitioner": 2, "Group": 5}
    for resource_type, expected in expected_counts.items():
        actual = sum(key.startswith(resource_type + "/") for key in resources)
        if actual != expected:
            errors.append(f"expected {expected} {resource_type} resources, found {actual}")

    assigned_patients = []
    care_team_patients = []
    for key, resource in resources.items():
        references = []
        if "subject" in resource:
            references.append(resource["subject"].get("reference"))
        if resource["resourceType"] == "CarePlan":
            references.extend(goal.get("reference") for goal in resource.get("goal", []))
            references.extend(team.get("reference") for team in resource.get("careTeam", []))
            references.extend(condition.get("reference") for condition in resource.get("addresses", []))
            references.append(resource.get("author", {}).get("reference"))
        if resource["resourceType"] == "Group":
            members = [member.get("entity", {}).get("reference") for member in resource.get("member", [])]
            if len(members) != 2:
                errors.append(f"{key}: expected exactly 2 patients, found {len(members)}")
            references.extend(members)
            assigned_patients.extend(members)
        if resource["resourceType"] == "CareTeam":
            subject = resource.get("subject", {}).get("reference")
            if not subject or not subject.startswith("Patient/"):
                errors.append(f"{key}: CareTeam subject must be a Patient")
            else:
                care_team_patients.append(subject)
            participants = resource.get("participant", [])
            if len(participants) != 1:
                errors.append(f"{key}: expected exactly 1 clinician, found {len(participants)}")
            references.extend(participant.get("member", {}).get("reference") for participant in participants)
        for reference in references:
            if reference and reference not in resources:
                errors.append(f"{key} references missing {reference}")

    if len(assigned_patients) != 10 or len(set(assigned_patients)) != 10:
        errors.append("each patient must be assigned to exactly one of the five teams")
    if len(care_team_patients) != 10 or len(set(care_team_patients)) != 10:
        errors.append("each patient must have exactly one patient-scoped CareTeam")

    for key, resource in resources.items():
        if resource["resourceType"] != "CarePlan":
            continue
        patient_reference = resource.get("subject", {}).get("reference")
        for team_reference in resource.get("careTeam", []):
            team = resources.get(team_reference.get("reference"), {})
            if team.get("subject", {}).get("reference") != patient_reference:
                errors.append(f"{key}: CareTeam subject does not match CarePlan subject")
    return errors


if __name__ == "__main__":
    paths = main()
    errs = validate(paths)
    if errs:
        print("VALIDATION ERRORS:")
        for e in errs:
            print(" -", e)
        raise SystemExit(1)
    combined_entries = []
    for path in paths:
        with open(path) as f:
            combined_entries.extend(json.load(f)["entry"])
    combined_path = os.path.join(OUT_DIR, "combined-patient-bundles.json")
    with open(combined_path, "w") as f:
        json.dump(
            {"resourceType": "Bundle", "type": "collection", "entry": combined_entries},
            f,
            indent=2,
        )
    print(f"Wrote and validated {len(paths)} FHIR bundles (10 patient + 1 team bundle):")
    for p in paths:
        print(" -", os.path.basename(p))
    print(" -", os.path.basename(combined_path), "(combined)")
