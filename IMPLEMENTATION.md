# Implementation

## Call path

1. The user confirms enrolled-voice consent and starts a browser call.
2. FastAPI creates a call session and assembles a self-compassion prompt with
   only facts extracted from prior calls.
3. Local NVIDIA vLLM generates one or two short spoken sentences with Nemotron
   3 Nano NVFP4. Thinking is disabled for live latency.
4. CUDA CSM conditions on the read-only 24 kHz reference and exact transcript,
   then returns a cloned WAV.
5. The browser accepts speech through SpeechRecognition or typed input.
6. Hangup asks Nemotron for strict JSON facts plus a one-line summary and saves
   them to SQLite for the next call.

## Runtime boundaries

`compose.nvidia.yml` is the only deployment definition. Both containers reserve
the NVIDIA GPU. Models and biometric enrollment stay outside Git and mount
read-only; only SQLite writes to the named data volume. The application runs
with a read-only root filesystem, dropped capabilities, and no-new-privileges.

CSM requests are serialized through one dedicated worker. Floating processor
inputs are converted to the loaded model dtype before generation, which avoids
the BF16/FP32 mismatch observed on GB10.

## Verification gates

`scripts/verify-nvidia.py` rejects a missing-consent call, opens a fresh self
call, validates the first greeting has no invented care-team history, generates
a real cloned greeting WAV, completes a live Nemotron turn, generates its WAV,
hangs up, verifies facts and summary persistence, and opens a second call using
that stored memory.
