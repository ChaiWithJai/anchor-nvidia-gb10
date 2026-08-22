"""On-box Whisper speech recognition for patient microphone turns."""

import asyncio
import io
import os
import wave
from concurrent.futures import ThreadPoolExecutor

from . import telemetry


class LocalWhisperBackend:
    def __init__(self):
        self.model_dir = os.environ.get(
            "CARELINE_STT_MODEL_DIR", "/models/whisper-tiny-en"
        )
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = asyncio.Lock()
        self._model = None
        self._processor = None

    def status(self) -> dict:
        return {
            "ready": os.path.isdir(self.model_dir),
            "engine": "Whisper tiny.en",
            "model_dir": self.model_dir,
            "local_only": True,
        }

    def _load(self) -> None:
        import torch
        from transformers import WhisperForConditionalGeneration, WhisperProcessor

        if not os.path.isdir(self.model_dir):
            raise RuntimeError("local STT model is not mounted")
        self._processor = WhisperProcessor.from_pretrained(
            self.model_dir, local_files_only=True
        )
        self._model = WhisperForConditionalGeneration.from_pretrained(
            self.model_dir,
            local_files_only=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )
        self._model.to("cuda" if torch.cuda.is_available() else "cpu")
        self._model.eval()

    @staticmethod
    def _decode_wav(payload: bytes):
        import numpy as np

        if len(payload) > 4 * 1024 * 1024:
            raise ValueError("audio turn exceeds 4 MB")
        try:
            with wave.open(io.BytesIO(payload), "rb") as source:
                channels = source.getnchannels()
                sample_width = source.getsampwidth()
                sample_rate = source.getframerate()
                frame_count = source.getnframes()
                frames = source.readframes(frame_count)
        except (wave.Error, EOFError) as error:
            raise ValueError("audio turn must be a PCM WAV") from error
        if channels != 1 or sample_width != 2 or not 8_000 <= sample_rate <= 48_000:
            raise ValueError("audio turn must be 16-bit mono PCM at 8-48 kHz")
        duration = frame_count / sample_rate
        if not 0.25 <= duration <= 30:
            raise ValueError("audio turn must be 0.25-30 seconds")
        samples = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
        if sample_rate != 16_000:
            target_count = max(1, round(len(samples) * 16_000 / sample_rate))
            samples = np.interp(
                np.linspace(0, len(samples) - 1, target_count),
                np.arange(len(samples)),
                samples,
            ).astype(np.float32)
        return samples, duration, frame_count

    def _transcribe(self, payload: bytes) -> dict:
        import torch

        samples, duration, frame_count = self._decode_wav(payload)
        inputs = self._processor(
            samples, sampling_rate=16_000, return_tensors="pt"
        ).input_features.to(
            device=self._model.device,
            dtype=next(self._model.parameters()).dtype,
        )
        with torch.inference_mode():
            generated = self._model.generate(inputs, max_new_tokens=120)
        text = self._processor.batch_decode(
            generated, skip_special_tokens=True
        )[0].strip()
        return {
            "text": text,
            "duration_seconds": round(duration, 3),
            "frame_count": frame_count,
            "engine": "Whisper tiny.en",
            "local_only": True,
        }

    async def transcribe(self, payload: bytes) -> dict:
        workload_id = telemetry.workload_started(
            "stt", "Local Whisper transcription", f"bytes={len(payload)}"
        )
        try:
            async with self._lock:
                if self._model is None:
                    await asyncio.get_running_loop().run_in_executor(
                        self._executor, self._load
                    )
                result = await asyncio.get_running_loop().run_in_executor(
                    self._executor, self._transcribe, payload
                )
            telemetry.workload_finished(workload_id)
            return result
        except Exception:
            telemetry.workload_finished(workload_id, "failed")
            raise


def get_backend() -> LocalWhisperBackend:
    return LocalWhisperBackend()
