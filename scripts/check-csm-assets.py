#!/usr/bin/env python3
"""Validate the exact Sesame processor inputs without loading model weights."""

import sys
import wave

import numpy as np
from transformers import AutoConfig, AutoProcessor, CsmForConditionalGeneration


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: check-csm-assets.py MODEL_DIR REF_WAV REF_TEXT")
    model_dir, reference_path, transcript_path = sys.argv[1:]
    config = AutoConfig.from_pretrained(model_dir, local_files_only=True)
    processor = AutoProcessor.from_pretrained(model_dir, local_files_only=True)
    assert config.model_type == "csm"
    assert processor.feature_extractor.sampling_rate == 24_000

    with wave.open(reference_path, "rb") as prompt:
        assert prompt.getnchannels() == 1
        assert prompt.getsampwidth() == 2
        assert prompt.getframerate() == 24_000
        audio = np.frombuffer(
            prompt.readframes(prompt.getnframes()), dtype="<i2"
        ).astype(np.float32) / 32768.0
    with open(transcript_path) as transcript_file:
        transcript = transcript_file.read().strip()
    assert transcript

    conversation = [
        {
            "role": "0",
            "content": [
                {"type": "text", "text": transcript},
                {"type": "audio", "path": audio},
            ],
        },
        {
            "role": "0",
            "content": [
                {"type": "text", "text": "The Sesame CUDA self voice is ready."}
            ],
        },
    ]
    inputs = processor.apply_chat_template(
        conversation, tokenize=True, return_dict=True
    )
    assert inputs["input_ids"].numel() > 0
    assert inputs["input_values"].numel() > 0
    shapes = {
        key: tuple(value.shape)
        for key, value in inputs.items()
        if hasattr(value, "shape")
    }
    print(f"Sesame ARM64 preprocessing passed: {shapes}")


if __name__ == "__main__":
    main()
