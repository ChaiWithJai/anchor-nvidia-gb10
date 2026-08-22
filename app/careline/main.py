"""CareLine API + demo UI server."""

import asyncio
import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

from . import agent_wake, context, llm, memory, store, telemetry, tts
from .agent import CallSession

from contextlib import asynccontextmanager

CLONE_TTS = tts.get_clone_backend()
VOICE_READY = False


@asynccontextmanager
async def lifespan(app):
    global VOICE_READY
    store.initialize()
    await CLONE_TTS.synthesize("Your digital twin is ready.")
    VOICE_READY = True
    yield
    VOICE_READY = False


app = FastAPI(title="Anchor NVIDIA GB10", version="2.1.0", lifespan=lifespan)

SESSIONS: dict[str, CallSession] = {}
WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")
ACCESS_KEY = os.environ.get("ANCHOR_DEMO_ACCESS_KEY", "").strip()
ACCESS_COOKIE = "anchor_demo_access"
if ACCESS_KEY and len(ACCESS_KEY) < 12:
    raise RuntimeError("ANCHOR_DEMO_ACCESS_KEY must contain at least 12 characters")


def _access_cookie_value() -> str:
    return hmac.new(ACCESS_KEY.encode(), b"anchor-demo-access", hashlib.sha256).hexdigest()


def _login_page(invalid: bool = False) -> HTMLResponse:
    error = '<p class="error">That access code is not valid.</p>' if invalid else ""
    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Anchor team access</title><style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#f3f5f2;color:#17211d;font-family:system-ui,sans-serif}}
main{{width:min(420px,calc(100% - 32px));padding:28px;background:#fff;border:1px solid #dce2dd;border-radius:8px}}
h1{{margin:0 0 8px;font-size:24px}}p{{color:#66736d;font-size:14px;line-height:1.5}}label{{display:block;margin:22px 0 7px;font-size:12px;font-weight:700}}
input{{width:100%;height:44px;box-sizing:border-box;padding:0 12px;border:1px solid #b9c3bd;border-radius:6px;font:inherit}}
button{{width:100%;height:44px;margin-top:12px;border:0;border-radius:6px;background:#1d6b4f;color:#fff;font-weight:700}}.error{{color:#c23d37}}
</style></head><body><main><h1>Anchor</h1><p>Private hackathon demonstration on NVIDIA GB10.</p>{error}
<form method="post" action="/auth"><label for="access_code">Team access code</label><input id="access_code" name="access_code" type="password" required autocomplete="current-password"><button type="submit">Enter demo</button></form>
</main></body></html>"""
    return HTMLResponse(
        body,
        status_code=401 if invalid else 200,
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'",
        },
    )


class StartCall(BaseModel):
    resident_id: str
    name: str
    mode: str = "care"  # "care" (Dorothy demo, Kokoro voice) | "self" (cloned voice)
    consent_confirmed: bool = False


class Turn(BaseModel):
    text: str
    mode: str = "care"
    consent_confirmed: bool = False


class AmbientSignal(BaseModel):
    resident_id: str
    goal_id: str | None = Field(default=None, max_length=80)
    type: str
    label: str
    value: int | float | str
    baseline: int | float | str
    unit: str = ""
    status: str


class GoalObservation(BaseModel):
    status: str = Field(min_length=3, max_length=12)
    value: int | float | str
    source: str = Field(default="clinician-console", min_length=2, max_length=40)

class PatientUpdate(BaseModel):

    display_name: str | None = Field(default=None, max_length=80)
    age_band: str | None = Field(default=None, max_length=20)
    program: str | None = Field(default=None, max_length=120)
    status: str | None = Field(default=None, max_length=30)
    risk_band: str | None = Field(default=None, max_length=30)
    next_check_in: str | None = Field(default=None, max_length=80)
    clinician_name: str | None = Field(default=None, max_length=80)


class CarePlanUpdate(BaseModel):
    author: str = Field(min_length=2, max_length=80)
    program: str = Field(min_length=2, max_length=120)
    today: list[str]
    check_in: list[str]
    options: list[str]
    on_call: str = Field(min_length=2, max_length=120)


class AlertResolution(BaseModel):
    clinician_id: str = Field(default="clinician-maya", min_length=2, max_length=80)
    resolved_by: str = Field(default="Dr. Maya Chen", min_length=2, max_length=80)
    note: str = Field(min_length=2, max_length=300)


class GoalClientHeartbeat(BaseModel):
    client_id: str = Field(min_length=8, max_length=80, pattern=r"^[A-Za-z0-9-]+$")
    surface: str = Field(min_length=1, max_length=40)
    connected: bool = True


def _validate_plan(body: CarePlanUpdate) -> None:
    if not 1 <= len(body.today) <= 8 or not 1 <= len(body.check_in) <= 8:
        raise HTTPException(400, "care plan requires 1-8 commitments and check-in topics")
    if not 3 <= len(body.options) <= 8:
        raise HTTPException(400, "care plan requires 3-8 clinician-approved options")
    if any(not item.strip() or len(item) > 240 for item in body.today + body.check_in + body.options):
        raise HTTPException(400, "care plan items must contain 1-240 characters")


@app.middleware("http")
async def require_demo_access(request: Request, call_next):
    if not ACCESS_KEY or request.url.path in {"/api/status", "/auth"}:
        return await call_next(request)
    supplied = request.cookies.get(ACCESS_COOKIE, "")
    if hmac.compare_digest(supplied, _access_cookie_value()):
        return await call_next(request)
    if request.method == "GET" and request.url.path in {"/", "/patient", "/goal"}:
        return _login_page()
    return Response(
        "Authentication required",
        status_code=401,
        media_type="text/plain",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.middleware("http")
async def record_live_request(request: Request, call_next):
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        telemetry.request_finished(request.url.path, 500, (time.monotonic() - started) * 1000)
        raise
    telemetry.request_finished(
        request.url.path, response.status_code, (time.monotonic() - started) * 1000
    )
    return response


@app.post("/auth")
async def authenticate(request: Request):
    if not ACCESS_KEY:
        return RedirectResponse("/", status_code=303)
    raw_body = await request.body()
    if len(raw_body) > 512:
        return _login_page(invalid=True)
    try:
        candidate = parse_qs(raw_body.decode()).get("access_code", [""])[0]
    except (UnicodeDecodeError, ValueError):
        return _login_page(invalid=True)
    if not hmac.compare_digest(candidate.encode(), ACCESS_KEY.encode()):
        return _login_page(invalid=True)
    forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        ACCESS_COOKIE,
        _access_cookie_value(),
        max_age=8 * 60 * 60,
        httponly=True,
        secure=forwarded_proto == "https",
        samesite="lax",
        path="/",
    )
    return response


@app.get("/")
async def index():
    return FileResponse(
        os.path.join(WEB_DIR, "index.html"),
        headers={"Cache-Control": "no-store, max-age=0"},
    )

@app.get("/patient")

async def patient_experience():
    return FileResponse(
        os.path.join(WEB_DIR, "patient.html"),
        headers={"Cache-Control": "no-store, max-age=0"},
    )



@app.get("/goal")
async def goal_operations():
    return FileResponse(
        os.path.join(WEB_DIR, "goal.html"),
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/goal-client.js")
async def goal_client_script():
    return FileResponse(
        os.path.join(WEB_DIR, "goal-client.js"),
        media_type="text/javascript",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.post("/api/goal/heartbeat")
async def goal_heartbeat(body: GoalClientHeartbeat, request: Request):
    telemetry.heartbeat(
        body.client_id,
        body.surface,
        request.client.host if request.client else None,
        request.headers.get("user-agent", ""),
        body.connected,
    )
    return {"accepted": True}


@app.get("/api/goal/snapshot")
def goal_snapshot():
    return telemetry.snapshot()


@app.get("/api/goal/events")
async def goal_events(request: Request):
    async def stream():
        while not await request.is_disconnected():
            snapshot = await asyncio.to_thread(telemetry.snapshot)
            yield f"data: {json.dumps(snapshot, separators=(',', ':'))}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/status")
async def status():
    nemotron_ready = await llm.ready()
    database = store.health()
    return {
        "ready": nemotron_ready and VOICE_READY and database["ready"],
        "runtime": "NVIDIA GB10",
        "llm": "Nemotron 3 Nano NVFP4",
        "voice": "Sesame CSM-1B CUDA",
        "nemotron_ready": nemotron_ready,
        "voice_ready": VOICE_READY,
        "agent_runtime": agent_wake.status(),
        "database_ready": database["ready"],
        "database": database,
        "shared_access": bool(ACCESS_KEY),
    }


@app.get("/api/context/{resident_id}")
async def recovery_context(resident_id: str):
    return context.get_context(resident_id)


@app.post("/api/context/signals")
async def record_ambient_signal(body: AmbientSignal):
    signals = context.set_signal(body.resident_id, body.model_dump(exclude={"resident_id"}))
    return {"signals": signals, "synthetic_demo_data": True}


@app.get("/api/reference-library")
async def reference_library():
    return {
        "references": store.reference_library(),
        "synthetic_demo_data": True,
    }


@app.post("/api/clinic/patients/{patient_id}/goals/{goal_id}/observations")
async def observe_goal(patient_id: str, goal_id: str, body: GoalObservation):
    if body.status not in {"met", "missed"}:
        raise HTTPException(400, "goal status must be met or missed")
    observation = store.record_goal_observation(
        patient_id, goal_id, body.status, body.value, body.source
    )
    if not observation:
        raise HTTPException(404, "active goal not found")
    return {
        "observation": observation,
        "patterns": store.goal_miss_patterns(patient_id),
    }


# Pre-opened sessions keyed by resident: the UI calls /api/calls/prepare on
# page load, so "Start call" returns a ready greeting (text + cached audio)
# instead of paying LLM + TTS latency while the user waits.
PREPARED: dict[str, tuple[CallSession, str]] = {}
TTS_CACHE: dict[str, bytes] = {}


@app.post("/api/calls/prepare")
async def prepare_call(body: StartCall):
    if body.mode != "self" or not body.consent_confirmed:
        raise HTTPException(400, "self-voice consent must be confirmed")
    session = CallSession(body.resident_id, body.name, mode=body.mode)
    greeting = await session.open_call()
    try:
        TTS_CACHE[greeting] = await CLONE_TTS.synthesize(greeting)
        while len(TTS_CACHE) > 32:
            TTS_CACHE.pop(next(iter(TTS_CACHE)))
    except Exception:
        import logging

        logging.getLogger("careline").exception("prepare: greeting TTS failed")
    PREPARED[body.resident_id] = (session, greeting)
    return {"prepared": True}


@app.post("/api/calls")
async def start_call(body: StartCall):
    if body.mode != "self" or not body.consent_confirmed:
        raise HTTPException(400, "self-voice consent must be confirmed")
    prepared = PREPARED.pop(body.resident_id, None)
    if prepared and prepared[0].mode == body.mode:
        session, greeting = prepared
    else:
        session = CallSession(body.resident_id, body.name, mode=body.mode)
        greeting = await session.open_call()
    SESSIONS[session.id] = session
    return {"call_id": session.id, "greeting": greeting}


@app.post("/api/calls/{call_id}/turn")
async def call_turn(call_id: str, body: Turn):
    session = SESSIONS.get(call_id)
    if not session:
        raise HTTPException(404, "unknown call")
    if not body.text.strip() or len(body.text) > 800:
        raise HTTPException(400, "turn must contain 1-800 characters")
    reply, alert = await session.turn(body.text)
    return {"reply": reply, "alert": alert, "concern_score": session.concern_score}


@app.post("/api/calls/{call_id}/end")
async def call_end(call_id: str):
    session = SESSIONS.pop(call_id, None)
    if not session:
        raise HTTPException(404, "unknown call")
    return await session.end()


@app.get("/api/residents/{resident_id}/memory")
async def resident_memory(resident_id: str):
    return {
        "facts": memory.recall(resident_id, limit=50),
        "calls": memory.recent_calls(resident_id),
    }




@app.get("/api/clinic/dashboard")
async def clinic_dashboard():
    return store.clinic_dashboard()


@app.get("/api/clinic/patients")
async def clinic_patients():
    return {"patients": store.list_patients(), "synthetic_demo_data": True}


@app.get("/api/clinic/patients/{patient_id}")
async def clinic_patient(patient_id: str):
    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "unknown clinic patient")
    return patient


@app.put("/api/clinic/patients/{patient_id}")
async def update_clinic_patient(patient_id: str, body: PatientUpdate):
    patient = store.update_patient(patient_id, body.model_dump(), "Dr. Maya Chen")
    if not patient:
        raise HTTPException(404, "unknown clinic patient")
    return patient


@app.put("/api/clinic/patients/{patient_id}/plan")
async def update_clinic_plan(patient_id: str, body: CarePlanUpdate):
    _validate_plan(body)
    plan = store.update_plan(patient_id, body.model_dump(), body.author)
    if not plan:
        raise HTTPException(404, "unknown clinic patient")
    return plan


@app.post("/api/clinic/alerts/{alert_id}/resolve")
async def resolve_clinic_alert(alert_id: str, body: AlertResolution):
    alert = store.resolve_alert(
        alert_id, body.resolved_by, body.note, body.clinician_id
    )
    if not alert:
        raise HTTPException(404, "open alert not found")
    return alert


@app.get("/api/clinic/activity")
async def clinic_activity():
    return {"events": store.recent_activity(), "synthetic_demo_data": True}
@app.get("/api/alerts")
async def alerts():
    return {"alerts": memory.list_alerts()}


@app.post("/api/tts")
async def synthesize(body: Turn):
    if body.mode != "self" or not body.consent_confirmed:
        raise HTTPException(400, "self-voice consent must be confirmed")
    cached = TTS_CACHE.pop(body.text, None)
    if cached:
        return Response(content=cached, media_type="audio/wav")
    try:
        wav = await CLONE_TTS.synthesize(body.text)
    except Exception as e:
        raise HTTPException(503, f"tts backend unavailable: {e}")
    return Response(content=wav, media_type="audio/wav")
