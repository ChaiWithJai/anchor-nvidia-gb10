"""NVIDIA CUDA voice cloning with a consented Sesame CSM-1B reference."""

import asyncio
import io
import os
import tempfile
import wave
from concurrent.futures import ThreadPoolExecutor


def _validate_reference(path: str) -> None:
    if not os.path.isfile(path):
        raise RuntimeError(f"voice reference not found: {path}")
    try:
        with wave.open(path, "rb") as audio:
            duration = audio.getnframes() / audio.getframerate()
            valid = (
                audio.getnchannels() == 1
                and audio.getsampwidth() == 2
                and audio.getframerate() == 24_000
                and 3 <= duration <= 10
            )
    except (wave.Error, EOFError) as exc:
        raise RuntimeError("voice reference must be a PCM WAV") from exc
    if not valid:
        raise RuntimeError("voice reference must be 3-10s, 24 kHz, 16-bit mono PCM")


class CudaCsmCloneBackend:
    """Serialize CSM inference on one CUDA worker to bound unified-memory use."""

    def __init__(self):
        self.model_dir = os.environ.get("CARELINE_CSM_MODEL_DIR", "/models/sesame-csm-1b")
        self.ref_audio = os.environ.get("CARELINE_SELF_REF_AUDIO", "/run/careline/self_ref.wav")
        self.ref_text_path = os.environ.get(
            "CARELINE_SELF_REF_TEXT", "/run/careline/self_ref.txt"
        )
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = asyncio.Lock()
        self._model = None
        self._processor = None
        self._ref_text = ""

    async def _run(self, fn, *args):
        return await asyncio.get_running_loop().run_in_executor(self._executor, fn, *args)

    def _load(self) -> None:
        import torch
        from transformers import AutoProcessor, CsmForConditionalGeneration

        if not torch.cuda.is_available():
            raise RuntimeError("NVIDIA CUDA is unavailable")
        _validate_reference(self.ref_audio)
        with open(self.ref_text_path, encoding="utf-8") as transcript:
            self._ref_text = transcript.read().strip()
        if not self._ref_text:
            raise RuntimeError("voice reference transcript is empty")
        self._processor = AutoProcessor.from_pretrained(self.model_dir, local_files_only=True)
        self._model = CsmForConditionalGeneration.from_pretrained(
            self.model_dir,
            device_map="cuda",
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        )

    def _generate(self, text: str) -> bytes:
        import numpy as np

        with wave.open(self.ref_audio, "rb") as prompt:
            reference_audio = np.frombuffer(
                prompt.readframes(prompt.getnframes()), dtype="<i2"
            ).astype(np.float32) / 32768.0
        conversation = [
            {
                "role": "0",
                "content": [
                    {"type": "text", "text": self._ref_text},
                    {"type": "audio", "path": reference_audio},
                ],
            },
            {"role": "0", "content": [{"type": "text", "text": text}]},
        ]
        inputs = self._processor.apply_chat_template(
            conversation, tokenize=True, return_dict=True
        ).to("cuda")
        model_dtype = next(self._model.parameters()).dtype
        inputs = {
            key: value.to(dtype=model_dtype) if value.is_floating_point() else value
            for key, value in inputs.items()
        }
        audio = self._model.generate(**inputs, output_audio=True)
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "clone.wav")
            self._processor.save_audio(audio, output)
            with open(output, "rb") as generated:
                payload = generated.read()
        if len(payload) <= 44:
            raise RuntimeError("CSM produced an empty WAV")
        with wave.open(io.BytesIO(payload), "rb") as generated:
            if generated.getframerate() != 24_000 or generated.getnframes() == 0:
                raise RuntimeError("CSM produced an invalid WAV")
        return payload

    async def synthesize(self, text: str) -> bytes:
        text = text.strip()
        if not text or len(text) > 500:
            raise ValueError("speech text must contain 1-500 characters")
        async with self._lock:
            if self._model is None:
                await self._run(self._load)
            return await self._run(self._generate, text)


def get_clone_backend() -> CudaCsmCloneBackend:
    return CudaCsmCloneBackend()
