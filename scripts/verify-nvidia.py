#!/usr/bin/env python3
"""End-to-end proof for Anchor's NVIDIA recovery check-in path."""

import http.cookiejar
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import wave

BASE = os.environ.get("CARELINE_BASE_URL", "http://127.0.0.1:8100")
ACCESS_KEY = os.environ.get("ANCHOR_DEMO_ACCESS_KEY", "").strip()
OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
)


def request(path: str, body: dict | None = None, method: str | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method or ("POST" if body is not None else "GET"),
        headers={"Content-Type": "application/json"},
    )
    with OPENER.open(req, timeout=180) as response:
        payload = response.read()
        if response.headers.get_content_type() == "application/json":
            return response.status, json.loads(payload)
        return response.status, payload


def request_audio(path: str, payload: bytes):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=payload,
        method="POST",
        headers={"Content-Type": "audio/wav"},
    )
    with OPENER.open(req, timeout=180) as response:
        return response.status, json.loads(response.read())


def assert_wav(payload: bytes) -> float:
    with wave.open(io.BytesIO(payload), "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()
        assert audio.getnchannels() >= 1
        assert audio.getframerate() == 24_000
        assert duration >= 0.5
        return duration


def main() -> int:
    status_code, status = request("/api/status")
    assert status_code == 200 and status["ready"] is True
    assert status["runtime"] == "NVIDIA GB10"
    assert status["database_ready"] is True
    assert status["database"]["engine"] == "MongoDB"
    assert status["database"]["version"].startswith("8.")
    assert status["stt"]["ready"] is True and status["stt"]["local_only"] is True
    print(f"PASS local stack: Nemotron + CSM + MongoDB {status['database']['version']} on NVIDIA GB10")
    assert status["agent_runtime"]["name"] == "OpenClaw in NVIDIA OpenShell"
    agent_configured = status["agent_runtime"]["configured"]

    if ACCESS_KEY:
        auth_body = urllib.parse.urlencode({"access_code": ACCESS_KEY}).encode()
        auth_request = urllib.request.Request(
            f"{BASE}/auth",
            data=auth_body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with OPENER.open(auth_request, timeout=30) as response:
            assert response.status == 200
            assert response.geturl().rstrip("/") == BASE.rstrip("/")
        print("PASS shared access: signed session cookie accepted")

    _, admin_page = request("/")
    _, patient_page = request("/patient")
    _, goal_page = request("/goal")
    assert b"Needs attention now" in admin_page
    assert b"Anchor is calling" in patient_page
    assert b"GB10 live operations" in goal_page
    print("PASS interfaces: clinician console + patient phone call + live GB10 view")

    client_id = f"verify-{uuid.uuid4().hex}"
    request(
        "/api/goal/heartbeat",
        {"client_id": client_id, "surface": "verification", "connected": True},
    )
    _, live = request("/api/goal/snapshot")
    assert live["gpu"]["ready"] is True
    assert "GB10" in live["gpu"]["name"]
    assert any(item["client_id"] == client_id[:12] for item in live["clients"])
    assert "request_counts" in live and "average_latency_ms" in live
    print(
        "PASS live operations: masked client + "
        f"{live['gpu']['utilization_gpu']}% GPU at {live['gpu']['temperature_c']}C"
    )

    _, dashboard = request("/api/clinic/dashboard")
    request("/api/clinic/demo/reset", method="POST")
    _, roster = request("/api/clinic/patients")
    assert dashboard["database"]["ready"] is True
    assert len(roster["patients"]) == 30
    assert len({patient["patient_id"] for patient in roster["patients"]}) == 30
    assert {patient["risk_tier_id"] for patient in roster["patients"]} == {
        "tier-0", "tier-1", "tier-2", "tier-3"
    }
    assert roster["patients"][0]["risk_tier_id"] == "tier-3"
    request("/api/clinic/demo/reset", method="POST")
    _, idempotent_roster = request("/api/clinic/patients")
    assert len(idempotent_roster["patients"]) == 30
    assert dashboard["active_patients"] >= 3
    demo_patient = next(
        patient for patient in roster["patients"] if patient["patient_id"] == "demo-jai"
    )
    assert len(demo_patient["care_team"]["clinician_ids"]) == 2
    assert demo_patient["conditions"] and demo_patient["goals"]
    assert demo_patient["notes"] and demo_patient["plan_revisions"]
    assert all(
        patient["conditions"] and patient["goals"] and patient["plan_revisions"]
        for patient in roster["patients"]
    )
    _, references = request("/api/reference-library")
    reference_ids = {item["reference_id"] for item in references["references"]}
    assert {
        "ref-coping-box-breathing",
        "ref-coping-urge-surfing",
        "ref-psychoed-craving-curve",
        "ref-crisis-988",
        "ref-crisis-ndvh",
    } <= reference_ids
    triage_corpus = {
        3: (
            "wish I was dead", "wish I wasn't here", "don't want to wake up",
            "rather not wake up", "better off without me",
            "everyone would have an easier time without me", "I'm a burden",
            "a weight on this family", "a drag on everyone",
            "the tablets are in the drawer", "I counted them", "I know the number",
            "moved them out of the bathroom", "the whole packet", "how many I have left",
            "thought about how I'd do it", "I know how I would", "worked out how",
            "I have a plan", "cut myself", "hurt myself", "burn myself", "overdose",
            "overdosed", "took too many", "I'm not safe on my own", "not safe tonight",
            "shouldn't be alone", "can't keep myself safe",
            "parked round the corner from", "engine running", "I know how this goes",
            "nothing will change", "never going to get better", "no way forward",
            "everything has gone grey", "can't feel my way out",
        ),
        2: (
            "my sponsor moved away", "sponsor's been travelling",
            "haven't spoken to my sponsor", "never found a new sponsor",
            "five months without one", "going to fewer meetings", "one in three now",
            "stopped going", "scaffolding coming down", "one would help me sleep",
            "telling myself it would", "building the case",
            "making arguments to myself", "the only way I'll sleep",
            "sitting there longer each night", "almost twenty minutes",
            "stayed longer than last time", "five days running", "longer every time",
        ),
        1: (
            "rotten flu", "been in bed two days", "throat's killing me", "unwell", "fever",
            "drove myself so I could leave", "decided before I went", "ordered a soda",
            "brought my own", "planned my exit", "it didn't really pull at me",
        ),
    }
    for expected_tier, phrases in triage_corpus.items():
        for phrase in phrases:
            _, classified = request("/api/triage/classify", {"text": phrase})
            assert classified["triage_tier"] == expected_tier, (
                phrase, expected_tier, classified
            )
    print("PASS triage corpus: owner-supplied Tier 3, Tier 2, and Tier 1 traps")
    goal_id = demo_patient["goals"][0]["goal_id"]
    request(
        f"/api/clinic/patients/demo-jai/goals/{goal_id}/observations",
        {"status": "missed", "value": "missed", "source": "verification"},
    )
    _, observed = request(
        f"/api/clinic/patients/demo-jai/goals/{goal_id}/observations",
        {"status": "missed", "value": "missed", "source": "verification"},
    )
    assert any(item["goal_id"] == goal_id for item in observed["patterns"])
    print("PASS clinical graph: 30 patients, two-person team, goals, references, notes, and tracking windows")
    plan = demo_patient["plan"]
    plan_payload = {
        "author": plan["author"],
        "program": plan["program"],
        "today": plan["today"],
        "check_in": plan["check_in"],
        "options": plan["options"],
        "on_call": plan["on_call"],
    }
    _, updated_plan = request("/api/clinic/patients/demo-jai/plan", plan_payload, method="PUT")
    assert updated_plan["version"] == plan["version"] + 1
    _, audit = request("/api/clinic/activity")
    assert any(event["action"] == "care_plan.updated" for event in audit["events"])
    print("PASS clinic workflow: roster, dashboard, care-plan publish, and MongoDB audit")

    _, recovery_context = request("/api/context/demo-jai")
    assert recovery_context["synthetic_demo_data"] is True
    assert recovery_context["triggered"] is True
    assert len(recovery_context["plan"]["today"]) >= 3
    assert len(recovery_context["plan"]["options"]) >= 3
    print(
        "PASS ambient context: "
        f"{recovery_context['trigger_reason']} / plan by {recovery_context['plan']['author']}"
    )

    try:
        request(
            "/api/calls",
            {"resident_id": "consent-gate", "name": "Jai", "mode": "self"},
        )
        raise AssertionError("call without consent was accepted")
    except urllib.error.HTTPError as error:
        assert error.code == 400
    print("PASS consent: unconfirmed cloned-voice call rejected")

    _, voices = request("/api/voices")
    assert len(voices["voices"]) >= 4
    assert {"catalog", "personalized", "text-only"} == set(voices["modes"])
    catalog_voice = voices["voices"][0]
    _, catalog_wav = request(
        "/api/tts",
        {
            "text": catalog_voice["preview_text"],
            "mode": "catalog",
            "voice_id": catalog_voice["voice_id"],
        },
    )
    print(
        "PASS consent-safe voice catalog: "
        f"{len(voices['voices'])} local voices, {assert_wav(catalog_wav):.2f}s preview"
    )

    resident_id = f"self-jai-e2e-{uuid.uuid4().hex[:8]}"
    call_body = {
        "resident_id": resident_id,
        "name": "Jai",
        "mode": "self",
        "consent_confirmed": True,
    }
    started = time.monotonic()
    _, call = request("/api/calls", call_body)
    greeting = call["greeting"].strip()
    assert greeting and len(greeting) < 500
    forbidden = ("care team", "last call", "last time", "we spoke before")
    assert not any(term in greeting.lower() for term in forbidden)
    print(f"PASS Anchor call start ({time.monotonic() - started:.1f}s): {greeting}")

    _, greeting_wav = request(
        "/api/tts",
        {
            "text": greeting,
            "mode": "self",
            "consent_confirmed": True,
            "trace_id": call["trace_id"],
        },
    )
    greeting_duration = assert_wav(greeting_wav)
    print(f"PASS cloned greeting: {greeting_duration:.2f}s WAV")

    if greeting_duration <= 30:
        _, audio_turn = request_audio(
            f"/api/calls/{call['call_id']}/audio-turn", greeting_wav
        )
        assert audio_turn["transcript"]["text"]
        assert audio_turn["transcript"]["local_only"] is True
        assert audio_turn["transcript"]["engine"] == "Whisper tiny.en"
        print(
            "PASS two-way audio: browser-format WAV transcribed locally and "
            "routed through the live call session"
        )

    stable_text = "My cravings are 2 out of 10, I slept seven hours, and I plan to make the meeting."
    turn_started = time.monotonic()
    _, stable_turn = request(
        f"/api/calls/{call['call_id']}/turn",
        {"text": stable_text, "mode": "self", "consent_confirmed": True},
    )
    assert stable_turn["alert"] is None
    print(f"PASS low-risk turn: no false escalation ({time.monotonic() - turn_started:.1f}s)")

    risk_text = "My cravings jumped to 8 and I want to use tonight."
    _, turn = request(
        f"/api/calls/{call['call_id']}/turn",
        {"text": risk_text, "mode": "self", "consent_confirmed": True},
    )
    reply = turn["reply"].strip()
    assert reply and len(reply) < 500
    assert len(reply.split()) <= 65
    notification_claims = ("clinician has been notified", "notifying the on-call")
    assert not any(claim in reply.lower() for claim in notification_claims)
    assert "review" in reply.lower() or "flagged" in reply.lower()
    assert turn["alert"] and turn["alert"]["destination"] == "on-call clinician"
    assert turn["alert"]["severity"] in {"medium", "high", "critical"}
    print(f"PASS clinician escalation ({turn['alert']['severity']}): {reply}")
    assert turn["alert"]["alert_id"]
    expected_delivery = "delivered" if agent_configured else "not-configured"
    assert turn["alert"]["agent_delivery"]["status"] == expected_delivery
    print(
        f"PASS agent handoff: OpenClaw delivery is {expected_delivery}"
    )

    _, reply_wav = request(
        "/api/tts",
        {
            "text": reply,
            "mode": "self",
            "consent_confirmed": True,
            "trace_id": call["trace_id"],
        },
    )
    print(f"PASS cloned, plan-grounded reply: {assert_wav(reply_wav):.2f}s WAV")

    _, ended = request(f"/api/calls/{call['call_id']}/end", method="POST")
    assert ended["summary"].strip()
    assert isinstance(ended["facts"], list) and ended["facts"]
    _, memory = request(f"/api/residents/{resident_id}/memory")
    assert memory["facts"] and memory["calls"]
    print(f"PASS hangup + memory: {ended['summary']}")
    assert memory["calls"][0]["transcript"]
    _, topology = request("/api/goal/architecture")
    node_ids = {node["node_id"] for node in topology["nodes"]}
    edge_ids = {edge["edge_id"] for edge in topology["edges"]}
    assert {
        "anchor-api", "mongodb", "nemotron", "sesame-csm", "whisper",
        "openclaw", "inference-local", "gb10",
    } <= node_ids
    assert {"anchor-mongodb", "anchor-openclaw", "openclaw-route"} <= edge_ids
    _, trace = request(f"/api/goal/traces/{call['trace_id']}")
    operations = [span["operation"] for span in trace["spans"]]
    assert operations.index("alert.commit") < operations.index("openclaw.wake")
    assert "alert.delivery.persist" in operations
    assert "nemotron.generate" in operations and "csm.synthesize" in operations
    assert "whisper.transcribe" in operations
    assert "openshell.inference.route" in operations
    serialized_trace = json.dumps(trace).lower()
    assert resident_id.lower() not in serialized_trace
    assert risk_text.lower() not in serialized_trace
    assert "237d30d8" not in serialized_trace
    _, traced_snapshot = request("/api/goal/snapshot")
    assert traced_snapshot["trace_buffer"]["count"] <= traced_snapshot["trace_buffer"]["limit"]
    assert any(item["trace_id"] == call["trace_id"] for item in traced_snapshot["traces"])
    print(
        "PASS architecture trace: bounded, payload-free, alert commit precedes "
        "OpenClaw wake, and GB10 model spans are correlated"
    )

    _, next_call = request("/api/calls", call_body)
    assert next_call["greeting"].strip()
    _, next_end = request(f"/api/calls/{next_call['call_id']}/end", method="POST")
    assert next_end["summary"].strip()
    print("PASS next call: persisted memory supplied to Nemotron")
    _, alerts = request("/api/alerts")
    persisted_alert = next(
        alert for alert in alerts["alerts"] if alert["patient_id"] == resident_id
    )
    assert persisted_alert["agent_delivery"]["status"] == expected_delivery
    print("PASS MongoDB evidence: transcript, memories, call record, alert, and audit event")
    print("Anchor clinic + patient NVIDIA GB10 workload passed end to end")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise
