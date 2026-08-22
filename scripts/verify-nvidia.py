#!/usr/bin/env python3
"""End-to-end proof for Anchor's NVIDIA recovery check-in path."""

import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
import wave

BASE = os.environ.get("CARELINE_BASE_URL", "http://127.0.0.1:8100")


def request(path: str, body: dict | None = None, method: str | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method or ("POST" if body is not None else "GET"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        payload = response.read()
        if response.headers.get_content_type() == "application/json":
            return response.status, json.loads(payload)
        return response.status, payload


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
    print("PASS runtime: Nemotron 3 Nano NVFP4 on NVIDIA GB10")

    _, recovery_context = request("/api/context/self-jai")
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
        {"text": greeting, "mode": "self", "consent_confirmed": True},
    )
    print(f"PASS cloned greeting: {assert_wav(greeting_wav):.2f}s WAV")

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
    assert turn["alert"] and turn["alert"]["destination"] == "on-call clinician"
    assert turn["alert"]["severity"] in {"medium", "high", "critical"}
    print(f"PASS clinician escalation ({turn['alert']['severity']}): {reply}")

    _, reply_wav = request(
        "/api/tts",
        {"text": reply, "mode": "self", "consent_confirmed": True},
    )
    print(f"PASS cloned, plan-grounded reply: {assert_wav(reply_wav):.2f}s WAV")

    _, ended = request(f"/api/calls/{call['call_id']}/end", method="POST")
    assert ended["summary"].strip()
    assert isinstance(ended["facts"], list) and ended["facts"]
    _, memory = request(f"/api/residents/{resident_id}/memory")
    assert memory["facts"] and memory["calls"]
    print(f"PASS hangup + memory: {ended['summary']}")

    _, next_call = request("/api/calls", call_body)
    assert next_call["greeting"].strip()
    _, next_end = request(f"/api/calls/{next_call['call_id']}/end", method="POST")
    assert next_end["summary"].strip()
    print("PASS next call: persisted memory supplied to Nemotron")
    print("Anchor NVIDIA GB10 workload passed end to end")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise
