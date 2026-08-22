"""Inbound speech-to-text.

One interface, several backends, chosen by CARELINE_STT_BACKEND:

    local     faster-whisper on this machine       (default)
    riva      NVIDIA Riva / NIM ASR over gRPC-HTTP (approved stack)
    browser   no-op: the client already sent text  (LEGACY — cloud call)

`browser` is the repo's original path and it is NOT local: Chrome streams the
microphone to Google. It stays here only so the existing front end keeps
working during migration. Do not ship a demo on it.

Every backend takes WAV bytes and returns plain text, so the call path does
not care which one is running.
"""
from __future__ import annotations
import asyncio, io, os, logging, wave

log = logging.getLogger("careline.stt")

BACKEND      = os.environ.get("CARELINE_STT_BACKEND", "local")
MODEL        = os.environ.get("CARELINE_STT_MODEL", "small")
DEVICE       = os.environ.get("CARELINE_STT_DEVICE", "auto")
COMPUTE      = os.environ.get("CARELINE_STT_COMPUTE", "int8")
MODEL_DIR    = os.environ.get("CARELINE_STT_MODEL_DIR", "")   # pre-staged, offline
RIVA_URL     = os.environ.get("CARELINE_RIVA_ASR_URL", "http://riva:50051/v1/asr")
MAX_SECONDS  = float(os.environ.get("CARELINE_STT_MAX_SECONDS", "180"))

# Seeding the decoder with in-domain words measurably improves recall on the
# exact terms the severity lexicon depends on.
PROMPT = ("Recovery check-in call. Vocabulary: craving, cravings, urge, urges, "
          "relapse, relapsed, slipped, sober, sobriety, withdrawal, trigger, "
          "triggered, IOP, outpatient, sponsor, meeting, counselor, counseling, "
          "detox, using, used, drink, drinking, pills, dose, overdose, sponsor, "
          "box breathing, urge surfing, check-in.")


class STTError(RuntimeError):
    pass


def _validate(audio: bytes) -> float:
    """Reject anything that is not sane PCM WAV before it reaches a model."""
    try:
        w = wave.open(io.BytesIO(audio))
    except Exception as exc:
        raise STTError("audio must be PCM WAV") from exc
    with w:
        if w.getsampwidth() != 2:
            raise STTError("audio must be 16-bit PCM")
        secs = w.getnframes() / float(w.getframerate() or 1)
    if secs <= 0:
        raise STTError("audio is empty")
    if secs > MAX_SECONDS:
        raise STTError(f"audio is {secs:.0f}s, limit {MAX_SECONDS:.0f}s")
    return secs


class LocalWhisperBackend:
    """faster-whisper, on this machine. Nothing leaves the box."""

    name = "local"

    def __init__(self):
        self._model = None
        self._lock = asyncio.Lock()

    def _load(self):
        if self._model is not None:
            return
        from faster_whisper import WhisperModel
        device = DEVICE
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"
        src = MODEL_DIR or MODEL
        log.info("loading faster-whisper %s (%s/%s)", src, device, COMPUTE)
        self._model = WhisperModel(src, device=device, compute_type=COMPUTE,
                                   local_files_only=bool(MODEL_DIR))

    def _run(self, audio: bytes) -> str:
        self._load()
        segs, _ = self._model.transcribe(
            io.BytesIO(audio), language="en", beam_size=5,
            vad_filter=True, vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False, initial_prompt=PROMPT)
        import re
        return re.sub(r"\s+", " ", " ".join(s.text.strip() for s in segs)).strip()

    async def transcribe(self, audio: bytes) -> str:
        _validate(audio)
        async with self._lock:                      # one decode at a time
            return await asyncio.to_thread(self._run, audio)


class RivaBackend:
    """NVIDIA Riva / NIM ASR. Same contract, remote-on-box service."""

    name = "riva"

    async def transcribe(self, audio: bytes) -> str:
        _validate(audio)
        import httpx
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(RIVA_URL,
                                 files={"file": ("turn.wav", audio, "audio/wav")},
                                 data={"language": "en-US"})
                r.raise_for_status()
                body = r.json()
        except Exception as exc:
            raise STTError(f"riva asr failed: {exc}") from exc
        for key in ("text", "transcript"):
            if isinstance(body.get(key), str):
                return body[key].strip()
        try:
            return body["results"][0]["alternatives"][0]["transcript"].strip()
        except Exception as exc:
            raise STTError(f"unexpected riva response: {str(body)[:200]}") from exc


class BrowserBackend:
    """LEGACY. The client transcribed already — this is a cloud call."""

    name = "browser"

    async def transcribe(self, audio: bytes) -> str:
        raise STTError(
            "CARELINE_STT_BACKEND=browser sends audio to Google via the client. "
            "There is no server-side transcription in this mode; the front end "
            "must POST text to /api/calls/{id}/turn instead.")


_BACKENDS = {"local": LocalWhisperBackend, "riva": RivaBackend, "browser": BrowserBackend}
_instance = None


def get_stt_backend():
    global _instance
    if _instance is None:
        cls = _BACKENDS.get(BACKEND)
        if cls is None:
            raise STTError(f"unknown CARELINE_STT_BACKEND={BACKEND!r}; "
                           f"expected one of {sorted(_BACKENDS)}")
        _instance = cls()
        if BACKEND == "browser":
            log.warning("STT backend 'browser' streams patient audio to Google — not local")
        else:
            log.info("STT backend: %s", BACKEND)
    return _instance


async def transcribe(audio: bytes) -> str:
    return await get_stt_backend().transcribe(audio)
