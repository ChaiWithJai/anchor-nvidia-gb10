#!/usr/bin/env python3
"""Prove a real text exchange, reconnection, and saved call through WebSocket."""
import asyncio
import http.cookiejar
import json
import os
import urllib.parse
import urllib.request

from websockets.asyncio.client import connect

BASE = os.environ.get("CARELINE_BASE_URL", "http://127.0.0.1:8100").rstrip("/")
COOKIES = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIES))


def request(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with OPENER.open(req, timeout=180) as response:
        return json.load(response)


async def main():
    key = os.environ.get("ANCHOR_DEMO_ACCESS_KEY", "")
    if key:
        req = urllib.request.Request(BASE + "/auth", data=urllib.parse.urlencode({"access_code": key}).encode())
        OPENER.open(req, timeout=30).close()
    call = request("/api/calls", {"resident_id": "demo-jai", "name": "Jai", "mode": "text-only"})
    path = "/api/calls/" + call["call_id"]
    url = ("wss" if BASE.startswith("https:") else "ws") + BASE[BASE.index(":"):] + path + "/ws"
    headers = {"Cookie": "; ".join(f"{cookie.name}={cookie.value}" for cookie in COOKIES)}
    ended = False
    submitted = "I slept seven hours and my cravings are two out of ten today."
    try:
        async with connect(url, additional_headers=headers) as ws:
            assert json.loads(await ws.recv())["type"] == "ready"
            await ws.send(json.dumps({"type": "turn", "text": submitted}))
            reply = json.loads(await asyncio.wait_for(ws.recv(), 180))
            assert reply["type"] == "reply" and reply["reply"].strip(), reply
            print("PASS WebSocket local model reply:", reply["reply"], flush=True)
        async with connect(url, additional_headers=headers) as ws:
            assert json.loads(await ws.recv())["type"] == "ready"
            await ws.send(json.dumps({"type": "end"}))
            result = json.loads(await asyncio.wait_for(ws.recv(), 180))
            assert result["type"] == "ended", result
            ended = True
        patient = request("/api/clinic/patients/demo-jai")
        # The same persisted call must appear in the clinician's patient history.
        saved = next((row for row in patient["recent_calls"] if row["call_id"] == call["call_id"]), None)
        assert saved is not None, "call absent from MongoDB-backed patient history"
        assert saved["status"] == "complete", "current call was not completed"
        assert {"role": "user", "text": submitted} in saved["transcript"], "current user turn was not saved"
        assert {"role": "assistant", "text": reply["reply"]} in saved["transcript"], "current assistant reply was not saved"
        print("PASS reconnect, call completion, and MongoDB transcript persistence", flush=True)
        print(json.dumps({"call_id": call["call_id"], "trace_id": call["trace_id"], "result": result}), flush=True)
    finally:
        if not ended:
            request(path + "/end", {})


if __name__ == "__main__":
    asyncio.run(main())
