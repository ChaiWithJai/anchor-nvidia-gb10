"""Outbound text-to-speech.

One entry point, several backends, chosen by CARELINE_TTS_BACKEND:

    kokoro       Kokoro-82M — fast, CPU-viable, PRESET voices (no cloning)
    csm          Sesame CSM-1B clone — delegates to the existing tts.py
    prerendered  play a cached clip, synthesise nothing
    auto         prerendered if a clip exists, else the configured fallback

Deliberately does not modify tts.py. The CSM path is the code that already
works; this wraps it rather than rewriting it.

Every backend takes text and returns WAV bytes, so the call path does not care
which is running.
"""
from __future__ import annotations
import asyncio, hashlib, io, logging, os, wave

log = logging.getLogger("careline.voice")

BACKEND      = os.environ.get("CARELINE_TTS_BACKEND", "kokoro")
FALLBACK     = os.environ.get("CARELINE_TTS_FALLBACK", "kokoro")
KOKORO_VOICE = os.environ.get("CARELINE_KOKORO_VOICE", "af_heart")
KOKORO_LANG  = os.environ.get("CARELINE_KOKORO_LANG", "a")     # 'a' = en-US
KOKORO_SPEED = float(os.environ.get("CARELINE_KOKORO_SPEED", "1.0"))
CLIP_DIR     = os.environ.get("CARELINE_TTS_CLIP_DIR", "/run/careline/clips")
SAMPLE_RATE  = 24000


class TTSError(RuntimeError):
    pass


def _pcm_to_wav(samples, rate: int = SAMPLE_RATE) -> bytes:
    """float32 [-1,1] -> 16-bit PCM WAV bytes."""
    import numpy as np
    a = np.asarray(samples, dtype="float32").squeeze()
    a = np.clip(a, -1.0, 1.0)
    pcm = (a * 32767.0).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


class KokoroBackend:
    """Kokoro-82M. Preset voices — this backend cannot clone a speaker.

    If the future-self mechanic matters for a scenario, pre-render it with CSM
    and serve it through PrerenderedBackend; Kokoro covers everything else.
    """

    name = "kokoro"

    def __init__(self):
        self._pipe = None
        self._lock = asyncio.Lock()

    def _load(self):
        if self._pipe is not None:
            return
        try:
            from kokoro import KPipeline
        except ImportError as exc:
            raise TTSError(
                "kokoro is not installed. `pip install kokoro soundfile` (and the "
                "espeak-ng system package). Note kokoro requires numpy>=2."
            ) from exc
        log.info("loading Kokoro (lang=%s voice=%s)", KOKORO_LANG, KOKORO_VOICE)
        self._pipe = KPipeline(lang_code=KOKORO_LANG)

    def _run(self, text: str) -> bytes:
        self._load()
        import numpy as np
        chunks = [audio for _, _, audio in
                  self._pipe(text, voice=KOKORO_VOICE, speed=KOKORO_SPEED)]
        if not chunks:
            raise TTSError("kokoro produced no audio")
        return _pcm_to_wav(np.concatenate([np.asarray(c).squeeze() for c in chunks]))

    async def synthesize(self, text: str) -> bytes:
        if not text.strip():
            raise TTSError("nothing to speak")
        async with self._lock:
            return await asyncio.to_thread(self._run, text)


class CsmCloneBackend:
    """Delegates to the existing tts.py. Unmodified."""

    name = "csm"

    async def synthesize(self, text: str) -> bytes:
        try:
            from . import tts
        except ImportError:
            import tts                                    # standalone use
        return await tts.get_clone_backend().synthesize(text)


class PrerenderedBackend:
    """Serve a cached clip keyed by the text. Synthesises nothing.

    This is how a cloned-voice demo stays safe on stage: render the scripted
    lines once, ahead of time, and play files. Nothing can fail live because
    nothing runs live.
    """

    name = "prerendered"

    @staticmethod
    def _path(text: str) -> str:
        key = hashlib.sha256(text.strip().lower().encode()).hexdigest()[:32]
        return os.path.join(CLIP_DIR, f"{key}.wav")

    def has_clip(self, text: str) -> bool:
        return os.path.exists(self._path(text))

    async def synthesize(self, text: str) -> bytes:
        p = self._path(text)
        if not os.path.exists(p):
            raise TTSError(f"no pre-rendered clip for this line ({os.path.basename(p)})")
        return await asyncio.to_thread(lambda: open(p, "rb").read())

    @classmethod
    def save(cls, text: str, audio: bytes) -> str:
        os.makedirs(CLIP_DIR, exist_ok=True)
        p = cls._path(text)
        with open(p, "wb") as f:
            f.write(audio)
        return p


class AutoBackend:
    """Pre-rendered when a clip exists, otherwise the configured fallback."""

    name = "auto"

    def __init__(self):
        self._pre = PrerenderedBackend()
        self._fb = _make(FALLBACK)

    async def synthesize(self, text: str) -> bytes:
        if self._pre.has_clip(text):
            return await self._pre.synthesize(text)
        return await self._fb.synthesize(text)


_BACKENDS = {"kokoro": KokoroBackend, "csm": CsmCloneBackend,
             "prerendered": PrerenderedBackend, "auto": AutoBackend}
_instance = None


def _make(name: str):
    cls = _BACKENDS.get(name)
    if cls is None:
        raise TTSError(f"unknown TTS backend {name!r}; expected one of {sorted(_BACKENDS)}")
    return cls()


def get_tts_backend():
    global _instance
    if _instance is None:
        _instance = _make(BACKEND)
        log.info("TTS backend: %s", BACKEND)
    return _instance


async def synthesize(text: str) -> bytes:
    return await get_tts_backend().synthesize(text)
