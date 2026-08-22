"""CareLine API + demo UI server."""

import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from . import context, llm, memory, tts
from .agent import CallSession

from contextlib import asynccontextmanager

CLONE_TTS = tts.get_clone_backend()
VOICE_READY = False


@asynccontextmanager
async def lifespan(app):
    global VOICE_READY
    await CLONE_TTS.synthesize("Your digital twin is ready.")
    VOICE_READY = True
    yield
    VOICE_READY = False


app = FastAPI(title="Anchor NVIDIA GB10", version="1.0.0", lifespan=lifespan)

SESSIONS: dict[str, CallSession] = {}
WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")


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
    type: str
    label: str
    value: int | float | str
    baseline: int | float | str
    unit: str = ""
    status: str


@app.get("/")
async def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


@app.get("/api/status")
async def status():
    nemotron_ready = await llm.ready()
    return {
        "ready": nemotron_ready and VOICE_READY,
        "runtime": "NVIDIA GB10",
        "llm": "Nemotron 3 Nano NVFP4",
        "voice": "Sesame CSM-1B CUDA",
        "nemotron_ready": nemotron_ready,
        "voice_ready": VOICE_READY,
    }


@app.get("/api/context/{resident_id}")
async def recovery_context(resident_id: str):
    return context.get_context(resident_id)


@app.post("/api/context/signals")
async def record_ambient_signal(body: AmbientSignal):
    signals = context.set_signal(body.resident_id, body.model_dump(exclude={"resident_id"}))
    return {"signals": signals, "synthetic_demo_data": True}


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
