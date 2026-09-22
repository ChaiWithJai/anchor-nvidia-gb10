# WebSocket messaging

Anchor accepts text messages through the existing FastAPI application. Each
message uses the same call handler, local Nemotron model, safety checks, and
MongoDB records as an HTTP call turn.

To try it in the browser, open `/patient`, choose **Text only** in voice
settings, and answer the call. The text input sends each turn over WebSocket.

First, create a call with `POST /api/calls`:

```json
{"resident_id":"demo-jai","name":"Jai","mode":"text-only"}
```

Second, use the returned `call_id` to connect to
`ws://127.0.0.1:8100/api/calls/{call_id}/ws`. Use `wss` when the application is
served over HTTPS. The server confirms the connection:

```json
{"type":"ready","call_id":"..."}
```

Third, send a message and wait for its reply:

```json
{"type":"turn","text":"I slept seven hours and my cravings are two out of ten."}
```

```json
{"type":"reply","reply":"...","alert":null,"concern_score":0}
```

Send `{"type":"end"}` when finished. The server saves the summary, memories,
and transcript through the existing completion handler, returns an `ended`
message, and closes the connection. `{"type":"ping"}` returns
`{"type":"pong"}`.

A dropped connection leaves the call open so the client can reconnect. End
the call explicitly through WebSocket or `POST /api/calls/{call_id}/end`.
Calls are held in application memory while active, as in the existing HTTP
workflow. An application restart does not restore an active call session.
Send one turn at a time, and don't retry a sent turn automatically after a
disconnect because the server may have processed it.

Messages have an 8 KiB limit, and turn text retains the existing 800-character
limit. Invalid messages return an error. Browser connections must have the
same origin host as the application. When shared access is enabled, the
WebSocket requires the same signed cookie as the HTTP API.

Run the live verification from a Python environment containing
`websockets==15.0.1`:

```bash
CARELINE_BASE_URL=http://127.0.0.1:8100 python scripts/verify-websocket.py
```

The verification sends a synthetic check-in, reconnects, completes the call,
and reads the transcript back from the clinician API. The optional OpenClaw
handoff retains its existing configuration described in `OPENSHLL.md`.

## Record verification in MLflow

Use a Python environment containing MLflow to run the command recorder on the
same host as the existing tracking server:

```bash
MLFLOW_TRACKING_URI=http://127.0.0.1:5210 \
  python scripts/track-command.py --name workload-verification -- \
  python3 scripts/verify-nvidia.py
```

The recorder creates a run in the `Anchor NVIDIA GB10` experiment and saves
the command log, duration, exit code, and a trace. `--parent-run RUN_ID`
groups verification runs under a deployment run. MLflow stays outside the
application container; the application keeps its existing `/goal` telemetry.
