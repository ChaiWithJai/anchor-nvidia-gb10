const anchorDb = db.getSiblingDB("anchor_fhir");

const patientsDocuments = [
  {
    "_id": "patient-01",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-01"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Jordan"
        ],
        "family": "Mercer",
        "text": "Jordan Mercer"
      }
    ],
    "gender": "male",
    "birthDate": "1988-03-14",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-917-555-0101",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "jordan.mercer@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "214 Cedar Walk, Brooklyn, NY 11215",
        "line": [
          "214 Cedar Walk"
        ],
        "city": "Brooklyn",
        "state": "NY",
        "postalCode": "11215",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "S",
          "display": "Never Married"
        }
      ],
      "text": "Never Married"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "employed_full_time",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "patient-02",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-02"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Casey"
        ],
        "family": "Bennett",
        "text": "Casey Bennett"
      }
    ],
    "gender": "female",
    "birthDate": "1992-07-22",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-917-555-0102",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "casey.bennett@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "88 Juniper Avenue, Queens, NY 11373",
        "line": [
          "88 Juniper Avenue"
        ],
        "city": "Queens",
        "state": "NY",
        "postalCode": "11373",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "S",
          "display": "Never Married"
        }
      ],
      "text": "Never Married"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "employed_part_time",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "patient-03",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-03"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Riley"
        ],
        "family": "Carter",
        "text": "Riley Carter"
      }
    ],
    "gender": "other",
    "birthDate": "1995-11-02",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-201-555-0103",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "riley.carter@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "31 Grove Terrace, Jersey City, NJ 07302",
        "line": [
          "31 Grove Terrace"
        ],
        "city": "Jersey City",
        "state": "NJ",
        "postalCode": "07302",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "S",
          "display": "Never Married"
        }
      ],
      "text": "Never Married"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "employed_full_time",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "patient-04",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-04"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Morgan"
        ],
        "family": "Diaz",
        "text": "Morgan Diaz"
      }
    ],
    "gender": "male",
    "birthDate": "1985-01-30",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-973-555-0104",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "morgan.diaz@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "407 Market Lane, Newark, NJ 07103",
        "line": [
          "407 Market Lane"
        ],
        "city": "Newark",
        "state": "NJ",
        "postalCode": "07103",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "D",
          "display": "Divorced"
        }
      ],
      "text": "Divorced"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "unemployed",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "patient-05",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-05"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Avery"
        ],
        "family": "Ellis",
        "text": "Avery Ellis"
      }
    ],
    "gender": "female",
    "birthDate": "1979-09-09",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-914-555-0105",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "avery.ellis@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "62 Parkview Road, Yonkers, NY 10701",
        "line": [
          "62 Parkview Road"
        ],
        "city": "Yonkers",
        "state": "NY",
        "postalCode": "10701",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "D",
          "display": "Divorced"
        }
      ],
      "text": "Divorced"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "employed_part_time",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "patient-06",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-06"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Quinn"
        ],
        "family": "Foster",
        "text": "Quinn Foster"
      }
    ],
    "gender": "male",
    "birthDate": "1990-05-17",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-973-555-0106",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "quinn.foster@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "119 Willow Street, Paterson, NJ 07501",
        "line": [
          "119 Willow Street"
        ],
        "city": "Paterson",
        "state": "NJ",
        "postalCode": "07501",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "M",
          "display": "Married"
        }
      ],
      "text": "Married"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "employed_full_time",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "patient-07",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-07"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Sage"
        ],
        "family": "Green",
        "text": "Sage Green"
      }
    ],
    "gender": "other",
    "birthDate": "1999-12-01",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-203-555-0107",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "sage.green@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "53 Chapel Court, New Haven, CT 06510",
        "line": [
          "53 Chapel Court"
        ],
        "city": "New Haven",
        "state": "CT",
        "postalCode": "06510",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "S",
          "display": "Never Married"
        }
      ],
      "text": "Never Married"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "student_part_time",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "patient-08",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-08"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Drew"
        ],
        "family": "Hayes",
        "text": "Drew Hayes"
      }
    ],
    "gender": "male",
    "birthDate": "1983-08-08",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-203-555-0108",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "drew.hayes@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "275 Harbor Drive, Stamford, CT 06901",
        "line": [
          "275 Harbor Drive"
        ],
        "city": "Stamford",
        "state": "CT",
        "postalCode": "06901",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "M",
          "display": "Married"
        }
      ],
      "text": "Married"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "employed_full_time",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "patient-09",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-09"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Reese"
        ],
        "family": "Irving",
        "text": "Reese Irving"
      }
    ],
    "gender": "female",
    "birthDate": "1997-02-19",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-718-555-0109",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "reese.irving@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "146 Belmont Avenue, Bronx, NY 10458",
        "line": [
          "146 Belmont Avenue"
        ],
        "city": "Bronx",
        "state": "NY",
        "postalCode": "10458",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "S",
          "display": "Never Married"
        }
      ],
      "text": "Never Married"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "employed_full_time",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "patient-10",
    "resourceType": "Patient",
    "identifiers": [
      {
        "system": "urn:anchor:demo-mrn",
        "value": "demo-patient-bridge"
      }
    ],
    "names": [
      {
        "use": "official",
        "given": [
          "Cameron"
        ],
        "family": "James",
        "text": "Cameron James"
      }
    ],
    "gender": "male",
    "birthDate": "1986-10-23",
    "telecom": [
      {
        "system": "phone",
        "value": "+1-914-555-0110",
        "use": "mobile"
      },
      {
        "system": "email",
        "value": "cameron.james@example.com",
        "use": "home"
      }
    ],
    "addresses": [
      {
        "use": "home",
        "type": "physical",
        "text": "90 Maple Crescent, White Plains, NY 10601",
        "line": [
          "90 Maple Crescent"
        ],
        "city": "White Plains",
        "state": "NY",
        "postalCode": "10601",
        "country": "US"
      }
    ],
    "maritalStatus": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
          "code": "L",
          "display": "Legally Separated"
        }
      ],
      "text": "Legally Separated"
    },
    "communications": [
      {
        "language": {
          "coding": [
            {
              "system": "urn:ietf:bcp:47",
              "code": "en",
              "display": "English"
            }
          ],
          "text": "English"
        },
        "preferred": true
      }
    ],
    "employmentStatus": "employed_part_time",
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  }
];
for (const document of patientsDocuments) {
  anchorDb.getCollection("patients").replaceOne(
    { _id: document._id },
    document,
    { upsert: true }
  );
}

const cliniciansDocuments = [
  {
    "_id": "clinician-01",
    "resourceType": "Practitioner",
    "givenNames": [
      "Maya"
    ],
    "familyName": "Chen",
    "displayName": "Dr. Maya Chen (seeded/fictional)",
    "identifiers": [
      {
        "system": "urn:anchor:synthetic-clinician-license",
        "value": "SYN-NY-MD-1001"
      }
    ],
    "telecom": [
      {
        "system": "phone",
        "value": "+1-212-555-0101",
        "use": "work"
      },
      {
        "system": "email",
        "value": "maya.chen@anchor-demo.example.com",
        "use": "work"
      }
    ],
    "qualifications": [
      {
        "code": {
          "coding": [
            {
              "system": "urn:anchor:synthetic-qualification",
              "code": "addiction-medicine",
              "display": "Addiction medicine physician"
            }
          ],
          "text": "Addiction medicine physician"
        }
      }
    ],
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  },
  {
    "_id": "clinician-02",
    "resourceType": "Practitioner",
    "givenNames": [
      "Liam"
    ],
    "familyName": "Patel",
    "displayName": "Dr. Liam Patel (seeded/fictional)",
    "identifiers": [
      {
        "system": "urn:anchor:synthetic-clinician-license",
        "value": "SYN-NY-MD-1002"
      }
    ],
    "telecom": [
      {
        "system": "phone",
        "value": "+1-212-555-0102",
        "use": "work"
      },
      {
        "system": "email",
        "value": "liam.patel@anchor-demo.example.com",
        "use": "work"
      }
    ],
    "qualifications": [
      {
        "code": {
          "coding": [
            {
              "system": "urn:anchor:synthetic-qualification",
              "code": "addiction-medicine",
              "display": "Addiction medicine physician"
            }
          ],
          "text": "Addiction medicine physician"
        }
      }
    ],
    "tags": [
      {
        "system": "urn:anchor:demo-data",
        "code": "synthetic"
      }
    ]
  }
];
for (const document of cliniciansDocuments) {
  anchorDb.getCollection("clinicians").replaceOne(
    { _id: document._id },
    document,
    { upsert: true }
  );
}

const careTeamsDocuments = [
  {
    "_id": "careteam-01",
    "resourceType": "CareTeam",
    "sourceGroupId": "patient-group-01",
    "patientCareTeamIds": [
      "careteam-patient-01",
      "careteam-patient-02"
    ],
    "name": "Harbor Recovery Team",
    "status": "active",
    "identifiers": [
      {
        "system": "urn:anchor:operational-care-team",
        "value": "ACT-01"
      }
    ],
    "categories": [
      {
        "text": "Behavioral health recovery management"
      }
    ],
    "period": {
      "start": "2026-01-01"
    },
    "telecom": [
      {
        "system": "phone",
        "value": "+1-212-555-0201",
        "use": "work"
      }
    ],
    "patientIds": [
      "patient-01",
      "patient-02"
    ],
    "clinicianId": "clinician-01",
    "clinicianRole": "Addiction medicine physician",
    "notes": [
      "Coverage hours: Mon-Fri 08:00-18:00.",
      "Anchor (voice check-in agent) is NOT a CareTeam member and is not represented here. It is a patient-facing adherence/check-in tool that reads this record's CarePlan and Goal resources — it never makes a clinical judgment, diagnosis, or care decision on this team's behalf."
    ]
  },
  {
    "_id": "careteam-02",
    "resourceType": "CareTeam",
    "sourceGroupId": "patient-group-02",
    "patientCareTeamIds": [
      "careteam-patient-03",
      "careteam-patient-04"
    ],
    "name": "Northstar Recovery Team",
    "status": "active",
    "identifiers": [
      {
        "system": "urn:anchor:operational-care-team",
        "value": "ACT-02"
      }
    ],
    "categories": [
      {
        "text": "Behavioral health recovery management"
      }
    ],
    "period": {
      "start": "2026-01-01"
    },
    "telecom": [
      {
        "system": "phone",
        "value": "+1-212-555-0202",
        "use": "work"
      }
    ],
    "patientIds": [
      "patient-03",
      "patient-04"
    ],
    "clinicianId": "clinician-01",
    "clinicianRole": "Addiction medicine physician",
    "notes": [
      "Coverage hours: Mon-Fri 09:00-19:00.",
      "Anchor (voice check-in agent) is NOT a CareTeam member and is not represented here. It is a patient-facing adherence/check-in tool that reads this record's CarePlan and Goal resources — it never makes a clinical judgment, diagnosis, or care decision on this team's behalf."
    ]
  },
  {
    "_id": "careteam-03",
    "resourceType": "CareTeam",
    "sourceGroupId": "patient-group-03",
    "patientCareTeamIds": [
      "careteam-patient-05",
      "careteam-patient-06"
    ],
    "name": "Bridgeway Recovery Team",
    "status": "active",
    "identifiers": [
      {
        "system": "urn:anchor:operational-care-team",
        "value": "ACT-03"
      }
    ],
    "categories": [
      {
        "text": "Behavioral health recovery management"
      }
    ],
    "period": {
      "start": "2026-02-01"
    },
    "telecom": [
      {
        "system": "phone",
        "value": "+1-212-555-0203",
        "use": "work"
      }
    ],
    "patientIds": [
      "patient-05",
      "patient-06"
    ],
    "clinicianId": "clinician-01",
    "clinicianRole": "Addiction medicine physician",
    "notes": [
      "Coverage hours: Mon-Sat 08:00-17:00.",
      "Anchor (voice check-in agent) is NOT a CareTeam member and is not represented here. It is a patient-facing adherence/check-in tool that reads this record's CarePlan and Goal resources — it never makes a clinical judgment, diagnosis, or care decision on this team's behalf."
    ]
  },
  {
    "_id": "careteam-04",
    "resourceType": "CareTeam",
    "sourceGroupId": "patient-group-04",
    "patientCareTeamIds": [
      "careteam-patient-07",
      "careteam-patient-08"
    ],
    "name": "Horizon Recovery Team",
    "status": "active",
    "identifiers": [
      {
        "system": "urn:anchor:operational-care-team",
        "value": "ACT-04"
      }
    ],
    "categories": [
      {
        "text": "Behavioral health recovery management"
      }
    ],
    "period": {
      "start": "2026-02-01"
    },
    "telecom": [
      {
        "system": "phone",
        "value": "+1-212-555-0204",
        "use": "work"
      }
    ],
    "patientIds": [
      "patient-07",
      "patient-08"
    ],
    "clinicianId": "clinician-02",
    "clinicianRole": "Addiction medicine physician",
    "notes": [
      "Coverage hours: Mon-Fri 08:00-20:00.",
      "Anchor (voice check-in agent) is NOT a CareTeam member and is not represented here. It is a patient-facing adherence/check-in tool that reads this record's CarePlan and Goal resources — it never makes a clinical judgment, diagnosis, or care decision on this team's behalf."
    ]
  },
  {
    "_id": "careteam-05",
    "resourceType": "CareTeam",
    "sourceGroupId": "patient-group-05",
    "patientCareTeamIds": [
      "careteam-patient-09",
      "careteam-patient-10"
    ],
    "name": "Pathfinder Recovery Team",
    "status": "active",
    "identifiers": [
      {
        "system": "urn:anchor:operational-care-team",
        "value": "ACT-05"
      }
    ],
    "categories": [
      {
        "text": "Behavioral health recovery management"
      }
    ],
    "period": {
      "start": "2026-03-01"
    },
    "telecom": [
      {
        "system": "phone",
        "value": "+1-212-555-0205",
        "use": "work"
      }
    ],
    "patientIds": [
      "patient-09",
      "patient-10"
    ],
    "clinicianId": "clinician-02",
    "clinicianRole": "Addiction medicine physician",
    "notes": [
      "Coverage hours: Mon-Sat 09:00-18:00.",
      "Anchor (voice check-in agent) is NOT a CareTeam member and is not represented here. It is a patient-facing adherence/check-in tool that reads this record's CarePlan and Goal resources — it never makes a clinical judgment, diagnosis, or care decision on this team's behalf."
    ]
  }
];
for (const document of careTeamsDocuments) {
  anchorDb.getCollection("careTeams").replaceOne(
    { _id: document._id },
    document,
    { upsert: true }
  );
}

const conditionsDocuments = [
  {
    "_id": "condition-01",
    "resourceType": "Condition",
    "patientId": "patient-01",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F10.20",
      "display": "Alcohol dependence, uncomplicated",
      "text": "Alcohol dependence, uncomplicated"
    },
    "onsetDateTime": "2026-05-01",
    "notes": [
      "DSM-5 moderate alcohol use disorder"
    ]
  },
  {
    "_id": "condition-02",
    "resourceType": "Condition",
    "patientId": "patient-02",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F11.20",
      "display": "Opioid dependence, uncomplicated",
      "text": "Opioid dependence, uncomplicated"
    },
    "onsetDateTime": "2026-04-10",
    "notes": [
      "DSM-5 severe opioid use disorder"
    ]
  },
  {
    "_id": "condition-03",
    "resourceType": "Condition",
    "patientId": "patient-03",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F14.10",
      "display": "Cocaine abuse, uncomplicated",
      "text": "Cocaine abuse, uncomplicated"
    },
    "onsetDateTime": "2026-06-05",
    "notes": [
      "DSM-5 mild stimulant (cocaine) use disorder"
    ]
  },
  {
    "_id": "condition-04",
    "resourceType": "Condition",
    "patientId": "patient-04",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F10.20",
      "display": "Alcohol dependence, uncomplicated",
      "text": "Alcohol dependence, uncomplicated"
    },
    "onsetDateTime": "2026-03-18",
    "notes": [
      "DSM-5 severe alcohol use disorder"
    ]
  },
  {
    "_id": "condition-04b",
    "resourceType": "Condition",
    "patientId": "patient-04",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F11.20",
      "display": "Opioid dependence, uncomplicated",
      "text": "Opioid dependence, uncomplicated"
    },
    "onsetDateTime": "2026-03-18",
    "notes": [
      "DSM-5 severe opioid use disorder — co-occurring, coded separately per current ICD-10-CM/DSM-5 guidance rather than a single 'polysubstance' code"
    ]
  },
  {
    "_id": "condition-05",
    "resourceType": "Condition",
    "patientId": "patient-05",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F10.20",
      "display": "Alcohol dependence, uncomplicated",
      "text": "Alcohol dependence, uncomplicated"
    },
    "onsetDateTime": "2026-02-27",
    "notes": [
      "DSM-5 severe alcohol use disorder"
    ]
  },
  {
    "_id": "condition-06",
    "resourceType": "Condition",
    "patientId": "patient-06",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F11.20",
      "display": "Opioid dependence, uncomplicated",
      "text": "Opioid dependence, uncomplicated"
    },
    "onsetDateTime": "2026-05-22",
    "notes": [
      "DSM-5 moderate opioid use disorder"
    ]
  },
  {
    "_id": "condition-07",
    "resourceType": "Condition",
    "patientId": "patient-07",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F12.10",
      "display": "Cannabis abuse, uncomplicated",
      "text": "Cannabis abuse, uncomplicated"
    },
    "onsetDateTime": "2026-06-30",
    "notes": [
      "DSM-5 mild cannabis use disorder"
    ]
  },
  {
    "_id": "condition-08",
    "resourceType": "Condition",
    "patientId": "patient-08",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F15.20",
      "display": "Other stimulant dependence, uncomplicated",
      "text": "Other stimulant dependence, uncomplicated"
    },
    "onsetDateTime": "2026-04-14",
    "notes": [
      "DSM-5 moderate stimulant use disorder"
    ]
  },
  {
    "_id": "condition-09",
    "resourceType": "Condition",
    "patientId": "patient-09",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F10.10",
      "display": "Alcohol abuse, uncomplicated",
      "text": "Alcohol abuse, uncomplicated"
    },
    "onsetDateTime": "2026-07-01",
    "notes": [
      "DSM-5 mild alcohol use disorder"
    ]
  },
  {
    "_id": "condition-10",
    "resourceType": "Condition",
    "patientId": "patient-10",
    "clinicalStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    },
    "verificationStatus": {
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    },
    "categories": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
            "code": "problem-list-item"
          }
        ]
      }
    ],
    "diagnosis": {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "F10.20",
      "display": "Alcohol dependence, uncomplicated",
      "text": "Alcohol dependence, uncomplicated"
    },
    "onsetDateTime": "2026-08-10",
    "notes": [
      "DSM-5 moderate alcohol use disorder — co-occurring referral to combined accountability + substance-treatment program"
    ]
  }
];
for (const document of conditionsDocuments) {
  anchorDb.getCollection("conditions").replaceOne(
    { _id: document._id },
    document,
    { upsert: true }
  );
}

const goalsDocuments = [
  {
    "_id": "goal-01",
    "resourceType": "Goal",
    "patientId": "patient-01",
    "lifecycleStatus": "active",
    "description": "Reduce drinking days to zero across a 30-day window",
    "targets": [
      {
        "measure": "self-reported drinking days/week",
        "dueDate": "2026-09-20"
      }
    ]
  },
  {
    "_id": "goal-02",
    "resourceType": "Goal",
    "patientId": "patient-02",
    "lifecycleStatus": "active",
    "description": "Complete intensive outpatient (IOP) program without unplanned discharge",
    "targets": [
      {
        "measure": "IOP session attendance rate",
        "dueDate": "2026-10-01"
      }
    ]
  },
  {
    "_id": "goal-03",
    "resourceType": "Goal",
    "patientId": "patient-03",
    "lifecycleStatus": "active",
    "description": "Identify and log craving triggers for 4 consecutive weeks",
    "targets": [
      {
        "measure": "trigger log entries/week",
        "dueDate": "2026-09-05"
      }
    ]
  },
  {
    "_id": "goal-04",
    "resourceType": "Goal",
    "patientId": "patient-04",
    "lifecycleStatus": "active",
    "description": "Complete IOP program with no positive screens",
    "targets": [
      {
        "measure": "screening result per session",
        "dueDate": "2026-11-01"
      }
    ]
  },
  {
    "_id": "goal-05",
    "resourceType": "Goal",
    "patientId": "patient-05",
    "lifecycleStatus": "active",
    "description": "Maintain abstinence through court review date",
    "targets": [
      {
        "measure": "self-reported drinking days + screening result",
        "dueDate": "2026-12-15"
      }
    ]
  },
  {
    "_id": "goal-06",
    "resourceType": "Goal",
    "patientId": "patient-06",
    "lifecycleStatus": "active",
    "description": "Attend every scheduled outpatient session for 8 weeks",
    "targets": [
      {
        "measure": "session attendance rate",
        "dueDate": "2026-09-30"
      }
    ]
  },
  {
    "_id": "goal-07",
    "resourceType": "Goal",
    "patientId": "patient-07",
    "lifecycleStatus": "active",
    "description": "Reduce use frequency to zero across a 4-week window",
    "targets": [
      {
        "measure": "self-reported use days/week",
        "dueDate": "2026-08-30"
      }
    ]
  },
  {
    "_id": "goal-08",
    "resourceType": "Goal",
    "patientId": "patient-08",
    "lifecycleStatus": "active",
    "description": "Sustain abstinence with negative screens for 60 days",
    "targets": [
      {
        "measure": "screening result per session",
        "dueDate": "2026-11-14"
      }
    ]
  },
  {
    "_id": "goal-09",
    "resourceType": "Goal",
    "patientId": "patient-09",
    "lifecycleStatus": "active",
    "description": "Limit drinking to zero on weeknights for 6 weeks",
    "targets": [
      {
        "measure": "self-reported drinking days/week",
        "dueDate": "2026-09-01"
      }
    ]
  },
  {
    "_id": "goal-10",
    "resourceType": "Goal",
    "patientId": "patient-10",
    "lifecycleStatus": "active",
    "description": "Maintain abstinence through the wait for program intake",
    "targets": [
      {
        "measure": "self-reported drinking days + daily check-in engagement",
        "dueDate": "2026-09-02"
      }
    ]
  }
];
for (const document of goalsDocuments) {
  anchorDb.getCollection("goals").replaceOne(
    { _id: document._id },
    document,
    { upsert: true }
  );
}

const carePlansDocuments = [
  {
    "_id": "careplan-01",
    "resourceType": "CarePlan",
    "patientId": "patient-01",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-01-2026"
      }
    ],
    "title": "Personalized recovery plan for Jordan Mercer",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-05-01",
    "authorClinicianId": "clinician-01",
    "careTeamId": "careteam-01",
    "patientCareTeamId": "careteam-patient-01",
    "conditionIds": [
      "condition-01"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan"
      }
    ],
    "period": {
      "start": "2026-05-01",
      "end": "2026-09-20"
    },
    "goalIds": [
      "goal-01"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "Weekly outpatient counseling session",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  },
  {
    "_id": "careplan-02",
    "resourceType": "CarePlan",
    "patientId": "patient-02",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-02-2026"
      }
    ],
    "title": "Personalized recovery plan for Casey Bennett",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-04-10",
    "authorClinicianId": "clinician-01",
    "careTeamId": "careteam-01",
    "patientCareTeamId": "careteam-patient-02",
    "conditionIds": [
      "condition-02"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan"
      }
    ],
    "period": {
      "start": "2026-04-10",
      "end": "2026-10-01"
    },
    "goalIds": [
      "goal-02"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "IOP attendance 3x/week",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 3,
        "status": "scheduled",
        "description": "Medication-assisted treatment follow-up with prescribing clinician",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  },
  {
    "_id": "careplan-03",
    "resourceType": "CarePlan",
    "patientId": "patient-03",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-03-2026"
      }
    ],
    "title": "Personalized recovery plan for Riley Carter",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-06-05",
    "authorClinicianId": "clinician-01",
    "careTeamId": "careteam-02",
    "patientCareTeamId": "careteam-patient-03",
    "conditionIds": [
      "condition-03"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan"
      }
    ],
    "period": {
      "start": "2026-06-05",
      "end": "2026-09-05"
    },
    "goalIds": [
      "goal-03"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "Biweekly outpatient counseling session",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  },
  {
    "_id": "careplan-04",
    "resourceType": "CarePlan",
    "patientId": "patient-04",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-04-2026"
      }
    ],
    "title": "Personalized recovery plan for Morgan Diaz",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-03-18",
    "authorClinicianId": "clinician-01",
    "careTeamId": "careteam-02",
    "patientCareTeamId": "careteam-patient-04",
    "conditionIds": [
      "condition-04",
      "condition-04b"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan (court-referred)"
      }
    ],
    "period": {
      "start": "2026-03-18",
      "end": "2026-11-01"
    },
    "goalIds": [
      "goal-04"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "IOP attendance 3x/week",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 3,
        "status": "scheduled",
        "description": "Court-mandated progress reporting",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  },
  {
    "_id": "careplan-05",
    "resourceType": "CarePlan",
    "patientId": "patient-05",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-05-2026"
      }
    ],
    "title": "Personalized recovery plan for Avery Ellis",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-02-27",
    "authorClinicianId": "clinician-01",
    "careTeamId": "careteam-03",
    "patientCareTeamId": "careteam-patient-05",
    "conditionIds": [
      "condition-05"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan (court-referred)"
      }
    ],
    "period": {
      "start": "2026-02-27",
      "end": "2026-12-15"
    },
    "goalIds": [
      "goal-05"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "IOP attendance 3x/week",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 3,
        "status": "scheduled",
        "description": "Court-mandated progress reporting",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  },
  {
    "_id": "careplan-06",
    "resourceType": "CarePlan",
    "patientId": "patient-06",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-06-2026"
      }
    ],
    "title": "Personalized recovery plan for Quinn Foster",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-05-22",
    "authorClinicianId": "clinician-01",
    "careTeamId": "careteam-03",
    "patientCareTeamId": "careteam-patient-06",
    "conditionIds": [
      "condition-06"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan"
      }
    ],
    "period": {
      "start": "2026-05-22",
      "end": "2026-09-30"
    },
    "goalIds": [
      "goal-06"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "Weekly outpatient counseling session",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  },
  {
    "_id": "careplan-07",
    "resourceType": "CarePlan",
    "patientId": "patient-07",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-07-2026"
      }
    ],
    "title": "Personalized recovery plan for Sage Green",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-06-30",
    "authorClinicianId": "clinician-02",
    "careTeamId": "careteam-04",
    "patientCareTeamId": "careteam-patient-07",
    "conditionIds": [
      "condition-07"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan"
      }
    ],
    "period": {
      "start": "2026-06-30",
      "end": "2026-08-30"
    },
    "goalIds": [
      "goal-07"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "Biweekly outpatient counseling session",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  },
  {
    "_id": "careplan-08",
    "resourceType": "CarePlan",
    "patientId": "patient-08",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-08-2026"
      }
    ],
    "title": "Personalized recovery plan for Drew Hayes",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-04-14",
    "authorClinicianId": "clinician-02",
    "careTeamId": "careteam-04",
    "patientCareTeamId": "careteam-patient-08",
    "conditionIds": [
      "condition-08"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan"
      }
    ],
    "period": {
      "start": "2026-04-14",
      "end": "2026-11-14"
    },
    "goalIds": [
      "goal-08"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "Weekly outpatient counseling session",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  },
  {
    "_id": "careplan-09",
    "resourceType": "CarePlan",
    "patientId": "patient-09",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-09-2026"
      }
    ],
    "title": "Personalized recovery plan for Reese Irving",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-07-01",
    "authorClinicianId": "clinician-02",
    "careTeamId": "careteam-05",
    "patientCareTeamId": "careteam-patient-09",
    "conditionIds": [
      "condition-09"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan"
      }
    ],
    "period": {
      "start": "2026-07-01",
      "end": "2026-09-01"
    },
    "goalIds": [
      "goal-09"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "Biweekly outpatient counseling session",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  },
  {
    "_id": "careplan-10",
    "resourceType": "CarePlan",
    "patientId": "patient-10",
    "identifiers": [
      {
        "system": "urn:anchor:demo-care-plan",
        "value": "ACP-10-2026"
      }
    ],
    "title": "Personalized recovery plan for Cameron James",
    "description": "Synthetic longitudinal behavioral-health recovery plan used for the Anchor demonstration.",
    "status": "active",
    "intent": "plan",
    "created": "2026-08-10",
    "authorClinicianId": "clinician-02",
    "careTeamId": "careteam-05",
    "patientCareTeamId": "careteam-patient-10",
    "conditionIds": [
      "condition-10"
    ],
    "categories": [
      {
        "coding": [
          {
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }
        ],
        "text": "Substance use disorder treatment plan — post-disclosure bridge to accountability program"
      }
    ],
    "period": {
      "start": "2026-08-10",
      "end": "2026-09-02"
    },
    "goalIds": [
      "goal-10"
    ],
    "activities": [
      {
        "position": 1,
        "status": "scheduled",
        "description": "Daily sobriety check-in via Anchor voice agent (bridge period only — does not replace the program)",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 2,
        "status": "scheduled",
        "description": "Scheduled intake at Riverside Accountability & Recovery Program (seeded/fictional) — combined BIP + substance treatment, self-referral accepted",
        "schedule": "Per individualized recovery schedule"
      },
      {
        "position": 3,
        "status": "scheduled",
        "description": "Any risk-shaped disclosure during a check-in routes to escalate_to_clinician() immediately — Anchor never assesses or acts on this itself",
        "schedule": "Per individualized recovery schedule"
      }
    ],
    "notes": [
      "Plan is clinician-authored synthetic demo data. Anchor may surface plan content but cannot diagnose, prescribe, or alter the plan."
    ]
  }
];
for (const document of carePlansDocuments) {
  anchorDb.getCollection("carePlans").replaceOne(
    { _id: document._id },
    document,
    { upsert: true }
  );
}

const voiceRiskTiersDocuments = [
  {
    "_id": "tier-1-mild",
    "rank": 1,
    "label": "Mild",
    "disposition": "resolve_in_conversation",
    "triggerSummary": "A single situational and clearly described response with no recurring pattern or current safety concern.",
    "action": {
      "name": "acknowledge_or_surface_reference",
      "gated": false,
      "gate": null
    },
    "eligibleReferenceCategories": [
      "coping_technique",
      "psychoeducation"
    ],
    "eligiblePatientFacingReferenceIds": [
      "ref-coping-box-breathing",
      "ref-coping-urge-surfing",
      "ref-psychoed-craving-curve"
    ],
    "clinicianOnlyReferenceIds": [],
    "reactivelyExcludedCategories": [
      "program_resource",
      "crisis_resource"
    ],
    "escalationRule": {
      "nextTierId": "tier-2-moderate",
      "consecutiveSameTriggerCount": 3,
      "missedGoalTargetThreshold": 2,
      "description": "Escalate when the same trigger or craving appears in three consecutive check-ins, or a goal target is missed more than once in the current tracking window."
    },
    "terminal": false,
    "keywordSignals": [
      "fine",
      "okay",
      "stuck to it",
      "tempted",
      "wanted a drink",
      "stressful day",
      "tired",
      "craving",
      "urge",
      "manageable"
    ],
    "keywordPolicy": "Human-review sense-check only; never classify from keyword matching alone."
  },
  {
    "_id": "tier-2-moderate",
    "rank": 2,
    "label": "Moderate",
    "disposition": "flag_pattern",
    "triggerSummary": "A recurring pattern across check-ins that merits clinician review, with nothing urgent in the current call.",
    "action": {
      "name": "flag_pattern_for_clinician",
      "gated": true,
      "gate": "OpenShell"
    },
    "eligibleReferenceCategories": [
      "coping_technique",
      "psychoeducation"
    ],
    "eligiblePatientFacingReferenceIds": [
      "ref-coping-box-breathing",
      "ref-coping-urge-surfing",
      "ref-psychoed-craving-curve"
    ],
    "clinicianOnlyReferenceIds": [],
    "reactivelyExcludedCategories": [
      "program_resource",
      "crisis_resource"
    ],
    "escalationRule": {
      "nextTierId": "tier-3-at-risk",
      "immediateOnAmbiguityOrSafetySignal": true,
      "description": "Escalate immediately when the current response is ambiguous, concerning, non-logical, or safety-relevant, regardless of pattern history."
    },
    "terminal": false,
    "keywordSignals": [
      "again",
      "every time",
      "keeps happening",
      "missed",
      "haven't been",
      "not working",
      "third time",
      "slipping",
      "hard to keep up",
      "frustrated"
    ],
    "keywordPolicy": "Human-review sense-check only; repetition across check-ins, not these words alone, qualifies the tier."
  },
  {
    "_id": "tier-3-at-risk",
    "rank": 3,
    "label": "At Risk",
    "disposition": "escalate",
    "triggerSummary": "An ambiguous or concerning response, or any explicit safety-relevant disclosure.",
    "action": {
      "name": "escalate_to_clinician",
      "gated": false,
      "gate": null,
      "alwaysOpen": true
    },
    "eligibleReferenceCategories": [
      "crisis_resource"
    ],
    "eligiblePatientFacingReferenceIds": [],
    "clinicianOnlyReferenceIds": [
      "ref-crisis-988",
      "ref-crisis-ndvh"
    ],
    "reactivelyExcludedCategories": [
      "program_resource"
    ],
    "escalationRule": {
      "nextTierId": null,
      "clinicianResolutionRequired": true,
      "description": "Terminal tier. It never self-resolves downward; only a clinician may close the escalation."
    },
    "terminal": true,
    "keywordSignals": [
      "hopeless",
      "no point",
      "can't do this anymore",
      "scared of myself",
      "not safe",
      "give up",
      "doesn't matter",
      "can't stop thinking about it",
      "hurt someone",
      "don't want to be here"
    ],
    "keywordPolicy": "Human-review sense-check only. Any specific or explicit safety disclosure escalates regardless of keyword matching."
  }
];
for (const document of voiceRiskTiersDocuments) {
  anchorDb.getCollection("voiceRiskTiers").replaceOne(
    { _id: document._id },
    document,
    { upsert: true }
  );
}

const healthHistoriesDocuments = [
  {
    "_id": "health-history-patient-01",
    "patientId": "patient-01",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p01-01",
        "domain": "routine_sleep_biological",
        "issueCode": "sleep_fragmentation",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-05-10",
        "lastObservedDate": "2026-08-15",
        "evidenceSource": "patient_reported",
        "summary": "Reports inconsistent sleep after stressful workdays, with tired evenings increasing vulnerability to cravings.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-01"
        ],
        "relatedGoalIds": [
          "goal-01"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p01-02",
        "domain": "high_risk_lifestyle_trigger",
        "issueCode": "halt_angry_anxious",
        "status": "monitoring",
        "severity": "mild",
        "firstObservedDate": "2026-06-02",
        "lastObservedDate": "2026-08-18",
        "evidenceSource": "voice_check_in",
        "summary": "Work-related tension has been described as an occasional evening craving trigger.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-01"
        ],
        "relatedGoalIds": [
          "goal-01"
        ],
        "recommendedReferenceIds": [
          "ref-coping-urge-surfing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p01-03",
        "domain": "emotional_psychological",
        "issueCode": "low_distress_tolerance",
        "status": "improving",
        "severity": "mild",
        "firstObservedDate": "2026-05-15",
        "lastObservedDate": "2026-08-11",
        "evidenceSource": "care_plan_review",
        "summary": "Uses structured check-ins to practice pausing before responding to acute stress.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 0,
        "relatedConditionIds": [
          "condition-01"
        ],
        "relatedGoalIds": [
          "goal-01"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      }
    ]
  },
  {
    "_id": "health-history-patient-02",
    "patientId": "patient-02",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p02-01",
        "domain": "routine_sleep_biological",
        "issueCode": "lack_daily_structure",
        "status": "improving",
        "severity": "moderate",
        "firstObservedDate": "2026-04-15",
        "lastObservedDate": "2026-08-14",
        "evidenceSource": "care_plan_review",
        "summary": "Intensive outpatient scheduling is being used to rebuild a consistent weekday routine.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 0,
        "relatedConditionIds": [
          "condition-02"
        ],
        "relatedGoalIds": [
          "goal-02"
        ],
        "recommendedReferenceIds": [
          "ref-psychoed-craving-curve"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p02-02",
        "domain": "routine_sleep_biological",
        "issueCode": "nutritional_depletion",
        "status": "monitoring",
        "severity": "mild",
        "firstObservedDate": "2026-04-20",
        "lastObservedDate": "2026-08-10",
        "evidenceSource": "patient_reported",
        "summary": "Irregular meals have occurred on high-demand treatment days and are tracked as a H.A.L.T. vulnerability.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-02"
        ],
        "relatedGoalIds": [
          "goal-02"
        ],
        "recommendedReferenceIds": [
          "ref-psychoed-craving-curve"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p02-03",
        "domain": "employment_housing_financial",
        "issueCode": "employment_disruption",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-05-01",
        "lastObservedDate": "2026-08-19",
        "evidenceSource": "patient_reported",
        "summary": "Treatment attendance and work scheduling create competing demands requiring ongoing coordination.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-02"
        ],
        "relatedGoalIds": [
          "goal-02"
        ],
        "recommendedReferenceIds": [],
        "applicableTierId": "tier-1-mild"
      }
    ]
  },
  {
    "_id": "health-history-patient-03",
    "patientId": "patient-03",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p03-01",
        "domain": "social_environment_isolation",
        "issueCode": "people_places_things_vulnerability",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-06-20",
        "lastObservedDate": "2026-08-20",
        "evidenceSource": "voice_pattern",
        "summary": "The same peer-group trigger has appeared in three consecutive check-ins and is ready for clinician pattern review.",
        "occurrenceCount": 3,
        "consecutiveCheckIns": 3,
        "relatedConditionIds": [
          "condition-03"
        ],
        "relatedGoalIds": [
          "goal-03"
        ],
        "recommendedReferenceIds": [
          "ref-coping-urge-surfing"
        ],
        "applicableTierId": "tier-2-moderate"
      },
      {
        "historyEntryId": "hh-p03-02",
        "domain": "social_environment_isolation",
        "issueCode": "social_anxiety_reengagement",
        "status": "monitoring",
        "severity": "mild",
        "firstObservedDate": "2026-07-01",
        "lastObservedDate": "2026-08-12",
        "evidenceSource": "patient_reported",
        "summary": "Reports discomfort reconnecting with sober social activities without familiar peers.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-03"
        ],
        "relatedGoalIds": [
          "goal-03"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p03-03",
        "domain": "routine_sleep_biological",
        "issueCode": "lack_daily_structure",
        "status": "active",
        "severity": "mild",
        "firstObservedDate": "2026-06-22",
        "lastObservedDate": "2026-08-16",
        "evidenceSource": "care_plan_review",
        "summary": "Unstructured weekend time is being tracked alongside the craving-trigger logging goal.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-03"
        ],
        "relatedGoalIds": [
          "goal-03"
        ],
        "recommendedReferenceIds": [
          "ref-psychoed-craving-curve"
        ],
        "applicableTierId": "tier-1-mild"
      }
    ]
  },
  {
    "_id": "health-history-patient-04",
    "patientId": "patient-04",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p04-01",
        "domain": "social_environment_isolation",
        "issueCode": "relationship_family_strain",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-03-15",
        "lastObservedDate": "2026-08-17",
        "evidenceSource": "patient_reported",
        "summary": "Family trust and communication remain strained while treatment and court requirements are underway.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-04",
          "condition-04b"
        ],
        "relatedGoalIds": [
          "goal-04"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p04-02",
        "domain": "employment_housing_financial",
        "issueCode": "financial_instability",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-04-01",
        "lastObservedDate": "2026-08-18",
        "evidenceSource": "patient_reported",
        "summary": "Treatment, transportation, and legal obligations are contributing to ongoing financial pressure.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-04",
          "condition-04b"
        ],
        "relatedGoalIds": [
          "goal-04"
        ],
        "recommendedReferenceIds": [],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p04-03",
        "domain": "emotional_psychological",
        "issueCode": "executive_dysfunction",
        "status": "monitoring",
        "severity": "mild",
        "firstObservedDate": "2026-04-12",
        "lastObservedDate": "2026-08-08",
        "evidenceSource": "care_plan_review",
        "summary": "Multiple appointments and reporting requirements create decision fatigue and scheduling difficulty.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 0,
        "relatedConditionIds": [
          "condition-04",
          "condition-04b"
        ],
        "relatedGoalIds": [
          "goal-04"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      }
    ]
  },
  {
    "_id": "health-history-patient-05",
    "patientId": "patient-05",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p05-01",
        "domain": "employment_housing_financial",
        "issueCode": "financial_instability",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-02-15",
        "lastObservedDate": "2026-08-18",
        "evidenceSource": "patient_reported",
        "summary": "Legal costs and reduced work availability are contributing to budget instability.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-05"
        ],
        "relatedGoalIds": [
          "goal-05"
        ],
        "recommendedReferenceIds": [],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p05-02",
        "domain": "social_environment_isolation",
        "issueCode": "relationship_family_strain",
        "status": "monitoring",
        "severity": "moderate",
        "firstObservedDate": "2026-03-01",
        "lastObservedDate": "2026-08-13",
        "evidenceSource": "patient_reported",
        "summary": "Rebuilding trust with family is an ongoing recovery concern.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-05"
        ],
        "relatedGoalIds": [
          "goal-05"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p05-03",
        "domain": "high_risk_lifestyle_trigger",
        "issueCode": "halt_tired",
        "status": "active",
        "severity": "mild",
        "firstObservedDate": "2026-05-01",
        "lastObservedDate": "2026-08-20",
        "evidenceSource": "voice_check_in",
        "summary": "Long days combining work, treatment, and reporting requirements occasionally produce high-risk fatigue.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-05"
        ],
        "relatedGoalIds": [
          "goal-05"
        ],
        "recommendedReferenceIds": [
          "ref-psychoed-craving-curve"
        ],
        "applicableTierId": "tier-1-mild"
      }
    ]
  },
  {
    "_id": "health-history-patient-06",
    "patientId": "patient-06",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p06-01",
        "domain": "employment_housing_financial",
        "issueCode": "appointment_adherence_barrier",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-06-10",
        "lastObservedDate": "2026-08-20",
        "evidenceSource": "voice_pattern",
        "summary": "Work-schedule conflicts affecting outpatient attendance have appeared in three consecutive check-ins.",
        "occurrenceCount": 3,
        "consecutiveCheckIns": 3,
        "relatedConditionIds": [
          "condition-06"
        ],
        "relatedGoalIds": [
          "goal-06"
        ],
        "recommendedReferenceIds": [],
        "applicableTierId": "tier-2-moderate"
      },
      {
        "historyEntryId": "hh-p06-02",
        "domain": "emotional_psychological",
        "issueCode": "executive_dysfunction",
        "status": "monitoring",
        "severity": "mild",
        "firstObservedDate": "2026-06-15",
        "lastObservedDate": "2026-08-09",
        "evidenceSource": "patient_reported",
        "summary": "Scheduling and short-term planning become more difficult during high-workload weeks.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-06"
        ],
        "relatedGoalIds": [
          "goal-06"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p06-03",
        "domain": "high_risk_lifestyle_trigger",
        "issueCode": "halt_tired",
        "status": "active",
        "severity": "mild",
        "firstObservedDate": "2026-06-18",
        "lastObservedDate": "2026-08-14",
        "evidenceSource": "voice_check_in",
        "summary": "Fatigue after schedule disruptions is tracked as a situational vulnerability.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-06"
        ],
        "relatedGoalIds": [
          "goal-06"
        ],
        "recommendedReferenceIds": [
          "ref-psychoed-craving-curve"
        ],
        "applicableTierId": "tier-1-mild"
      }
    ]
  },
  {
    "_id": "health-history-patient-07",
    "patientId": "patient-07",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p07-01",
        "domain": "emotional_psychological",
        "issueCode": "anhedonia_emotional_flatness",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-07-01",
        "lastObservedDate": "2026-08-18",
        "evidenceSource": "patient_reported",
        "summary": "Previously enjoyable sober activities currently feel less rewarding during early recovery.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-07"
        ],
        "relatedGoalIds": [
          "goal-07"
        ],
        "recommendedReferenceIds": [
          "ref-psychoed-craving-curve"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p07-02",
        "domain": "social_environment_isolation",
        "issueCode": "social_isolation",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-07-05",
        "lastObservedDate": "2026-08-19",
        "evidenceSource": "patient_reported",
        "summary": "Reducing contact with substance-using peers has left evenings with limited supportive contact.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-07"
        ],
        "relatedGoalIds": [
          "goal-07"
        ],
        "recommendedReferenceIds": [
          "ref-coping-urge-surfing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p07-03",
        "domain": "social_environment_isolation",
        "issueCode": "social_anxiety_reengagement",
        "status": "monitoring",
        "severity": "mild",
        "firstObservedDate": "2026-07-12",
        "lastObservedDate": "2026-08-11",
        "evidenceSource": "voice_check_in",
        "summary": "Sober social settings can feel uncomfortable but remain manageable within the call.",
        "occurrenceCount": 1,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-07"
        ],
        "relatedGoalIds": [
          "goal-07"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      }
    ]
  },
  {
    "_id": "health-history-patient-08",
    "patientId": "patient-08",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p08-01",
        "domain": "routine_sleep_biological",
        "issueCode": "sleep_fragmentation",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-04-08",
        "lastObservedDate": "2026-08-19",
        "evidenceSource": "patient_reported",
        "summary": "Irregular sleep timing and nighttime waking contribute to daytime fatigue.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-08"
        ],
        "relatedGoalIds": [
          "goal-08"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p08-02",
        "domain": "routine_sleep_biological",
        "issueCode": "nutritional_depletion",
        "status": "improving",
        "severity": "mild",
        "firstObservedDate": "2026-04-15",
        "lastObservedDate": "2026-08-10",
        "evidenceSource": "care_plan_review",
        "summary": "Meal consistency is improving but remains part of relapse-vulnerability monitoring.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 0,
        "relatedConditionIds": [
          "condition-08"
        ],
        "relatedGoalIds": [
          "goal-08"
        ],
        "recommendedReferenceIds": [
          "ref-psychoed-craving-curve"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p08-03",
        "domain": "emotional_psychological",
        "issueCode": "executive_dysfunction",
        "status": "monitoring",
        "severity": "moderate",
        "firstObservedDate": "2026-04-20",
        "lastObservedDate": "2026-08-16",
        "evidenceSource": "patient_reported",
        "summary": "Brain fog and decision fatigue make multi-step daily tasks harder during periods of poor sleep.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-08"
        ],
        "relatedGoalIds": [
          "goal-08"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      }
    ]
  },
  {
    "_id": "health-history-patient-09",
    "patientId": "patient-09",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p09-01",
        "domain": "high_risk_lifestyle_trigger",
        "issueCode": "halt_lonely",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-06-10",
        "lastObservedDate": "2026-08-20",
        "evidenceSource": "voice_pattern",
        "summary": "Lonely, unstructured weeknights have appeared in three consecutive check-ins and are ready for clinician pattern review.",
        "occurrenceCount": 3,
        "consecutiveCheckIns": 3,
        "relatedConditionIds": [
          "condition-09"
        ],
        "relatedGoalIds": [
          "goal-09"
        ],
        "recommendedReferenceIds": [
          "ref-coping-urge-surfing"
        ],
        "applicableTierId": "tier-2-moderate"
      },
      {
        "historyEntryId": "hh-p09-02",
        "domain": "high_risk_lifestyle_trigger",
        "issueCode": "halt_angry_anxious",
        "status": "monitoring",
        "severity": "mild",
        "firstObservedDate": "2026-06-18",
        "lastObservedDate": "2026-08-12",
        "evidenceSource": "patient_reported",
        "summary": "Work frustration is an occasional weeknight trigger but has not formed a consecutive pattern.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-09"
        ],
        "relatedGoalIds": [
          "goal-09"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p09-03",
        "domain": "routine_sleep_biological",
        "issueCode": "lack_daily_structure",
        "status": "active",
        "severity": "mild",
        "firstObservedDate": "2026-06-22",
        "lastObservedDate": "2026-08-15",
        "evidenceSource": "care_plan_review",
        "summary": "Weeknight downtime lacks consistent planned activities and overlaps with the abstinence goal window.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-09"
        ],
        "relatedGoalIds": [
          "goal-09"
        ],
        "recommendedReferenceIds": [
          "ref-psychoed-craving-curve"
        ],
        "applicableTierId": "tier-1-mild"
      }
    ]
  },
  {
    "_id": "health-history-patient-10",
    "patientId": "patient-10",
    "asOfDate": "2026-08-22",
    "synthetic": true,
    "entries": [
      {
        "historyEntryId": "hh-p10-01",
        "domain": "employment_housing_financial",
        "issueCode": "program_access_gap",
        "status": "active",
        "severity": "moderate",
        "firstObservedDate": "2026-07-20",
        "lastObservedDate": "2026-08-20",
        "evidenceSource": "care_plan_review",
        "summary": "The period before scheduled program intake creates a temporary gap in structured support.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-10"
        ],
        "relatedGoalIds": [
          "goal-10"
        ],
        "recommendedReferenceIds": [],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p10-02",
        "domain": "social_environment_isolation",
        "issueCode": "social_isolation",
        "status": "monitoring",
        "severity": "moderate",
        "firstObservedDate": "2026-07-25",
        "lastObservedDate": "2026-08-18",
        "evidenceSource": "patient_reported",
        "summary": "Limited support during the intake waiting period makes evening check-ins especially important.",
        "occurrenceCount": 2,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-10"
        ],
        "relatedGoalIds": [
          "goal-10"
        ],
        "recommendedReferenceIds": [
          "ref-coping-urge-surfing"
        ],
        "applicableTierId": "tier-1-mild"
      },
      {
        "historyEntryId": "hh-p10-03",
        "domain": "high_risk_lifestyle_trigger",
        "issueCode": "halt_angry_anxious",
        "status": "active",
        "severity": "mild",
        "firstObservedDate": "2026-07-28",
        "lastObservedDate": "2026-08-16",
        "evidenceSource": "voice_check_in",
        "summary": "Anxiety about the upcoming program transition is currently situational and clearly described.",
        "occurrenceCount": 1,
        "consecutiveCheckIns": 1,
        "relatedConditionIds": [
          "condition-10"
        ],
        "relatedGoalIds": [
          "goal-10"
        ],
        "recommendedReferenceIds": [
          "ref-coping-box-breathing"
        ],
        "applicableTierId": "tier-1-mild"
      }
    ]
  }
];
for (const document of healthHistoriesDocuments) {
  anchorDb.getCollection("healthHistories").replaceOne(
    { _id: document._id },
    document,
    { upsert: true }
  );
}
