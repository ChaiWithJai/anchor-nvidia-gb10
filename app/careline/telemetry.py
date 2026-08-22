"""In-process live operations telemetry for the GB10 demo runtime."""

from __future__ import annotations

import os
import json
import subprocess
import threading
import time
import uuid
from collections import Counter, deque
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any


STARTED_AT = time.monotonic()
CLIENT_TTL_SECONDS = int(os.environ.get("CARELINE_CLIENT_TTL_SECONDS", "20"))
_LOCK = threading.RLock()
_CLIENTS: dict[str, dict[str, Any]] = {}
_WORKLOADS: dict[str, dict[str, Any]] = {}
_EVENTS: deque[dict[str, Any]] = deque(maxlen=80)
_REQUESTS: Counter[str] = Counter()
_GPU_CACHE: dict[str, Any] | None = None
_GPU_SAMPLED_MONOTONIC = 0.0
_TRACE_LIMIT = int(os.environ.get("CARELINE_TRACE_LIMIT", "40"))
_TRACE_IDS: deque[str] = deque()
_TRACES: dict[str, dict[str, Any]] = {}
_WORKLOAD_SPANS: dict[str, tuple[str, str]] = {}
_CURRENT_TRACE: ContextVar[str | None] = ContextVar("anchor_trace", default=None)
_CURRENT_SPAN: ContextVar[str | None] = ContextVar("anchor_span", default=None)
_TOPOLOGY_PATH = os.path.join(os.path.dirname(__file__), "architecture-topology.json")
with open(_TOPOLOGY_PATH, encoding="utf-8") as _topology_source:
    _TOPOLOGY = json.load(_topology_source)
_LATENCY_MS: dict[str, deque[float]] = {
    "http": deque(maxlen=120),
    "nemotron": deque(maxlen=60),
    "csm": deque(maxlen=60),
}

_SAFE_PROOF_KEYS = {
    "acknowledged",
    "collection",
    "correlation",
    "delivery_status",
    "ordering",
    "route",
    "sandbox",
    "sampled_at",
    "utilization_gpu",
    "power_draw_w",
    "clock_sm_mhz",
}


def _safe_proof(metadata: dict[str, Any] | None) -> dict[str, Any]:
    return {
        key: value
        for key, value in (metadata or {}).items()
        if key in _SAFE_PROOF_KEYS
        and isinstance(value, (str, int, float, bool, type(None)))
    }


def start_trace(surface: str) -> str:
    trace_id = uuid.uuid4().hex[:16]
    with _LOCK:
        if len(_TRACE_IDS) >= _TRACE_LIMIT:
            expired = _TRACE_IDS.popleft()
            _TRACES.pop(expired, None)
        _TRACE_IDS.append(trace_id)
        _TRACES[trace_id] = {
            "trace_id": trace_id,
            "surface": surface[:40],
            "started_at": _iso_now(),
            "started_monotonic": time.monotonic(),
            "finished_at": None,
            "duration_ms": None,
            "outcome": "active",
            "spans": [],
        }
    return trace_id


@contextmanager
def trace_scope(trace_id: str | None):
    token = _CURRENT_TRACE.set(trace_id if trace_id in _TRACES else None)
    try:
        yield
    finally:
        _CURRENT_TRACE.reset(token)


def finish_trace(trace_id: str, outcome: str = "complete") -> None:
    with _LOCK:
        trace = _TRACES.get(trace_id)
        if not trace:
            return
        trace["finished_at"] = _iso_now()
        trace["duration_ms"] = round(
            (time.monotonic() - trace["started_monotonic"]) * 1000, 1
        )
        trace["outcome"] = (
            "failed"
            if outcome == "complete"
            and any(item["outcome"] == "failed" for item in trace["spans"])
            else outcome
        )


def _start_span(
    operation: str,
    component: str,
    proof_area: str,
    edge_id: str | None,
    metadata: dict[str, Any] | None,
) -> tuple[str, str] | None:
    trace_id = _CURRENT_TRACE.get()
    if not trace_id:
        return None
    span_id = uuid.uuid4().hex[:12]
    with _LOCK:
        trace = _TRACES.get(trace_id)
        if not trace:
            return None
        trace["spans"].append(
            {
                "span_id": span_id,
                "parent_span_id": _CURRENT_SPAN.get(),
                "operation": operation[:80],
                "component": component[:40],
                "edge_id": edge_id,
                "proof_area": proof_area,
                "started_at": _iso_now(),
                "started_monotonic": time.monotonic(),
                "finished_at": None,
                "duration_ms": None,
                "outcome": "active",
                "proof": _safe_proof(metadata),
            }
        )
    return trace_id, span_id


def _finish_span(
    trace_id: str,
    span_id: str,
    outcome: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    with _LOCK:
        trace = _TRACES.get(trace_id)
        if not trace:
            return
        span = next(
            (item for item in trace["spans"] if item["span_id"] == span_id), None
        )
        if not span:
            return
        span["finished_at"] = _iso_now()
        span["duration_ms"] = round(
            (time.monotonic() - span.pop("started_monotonic")) * 1000, 1
        )
        span["outcome"] = outcome
        span["proof"].update(_safe_proof(metadata))


@contextmanager
def span(
    operation: str,
    component: str,
    proof_area: str,
    edge_id: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    started = _start_span(operation, component, proof_area, edge_id, metadata)
    if not started:
        yield None
        return
    trace_id, span_id = started
    token = _CURRENT_SPAN.set(span_id)
    try:
        yield span_id
    except Exception:
        _finish_span(trace_id, span_id, "failed")
        raise
    else:
        _finish_span(trace_id, span_id, "complete", metadata)
    finally:
        _CURRENT_SPAN.reset(token)


def architecture() -> dict[str, Any]:
    return json.loads(json.dumps(_TOPOLOGY))


def trace_detail(trace_id: str) -> dict[str, Any] | None:
    with _LOCK:
        trace = _TRACES.get(trace_id)
        if not trace:
            return None
        public = {
            key: value
            for key, value in trace.items()
            if key != "started_monotonic"
        }
        public["spans"] = [
            {key: value for key, value in item.items() if key != "started_monotonic"}
            for item in trace["spans"]
        ]
        return json.loads(json.dumps(public))


def _trace_summaries() -> list[dict[str, Any]]:
    summaries = []
    for trace_id in reversed(_TRACE_IDS):
        trace = _TRACES.get(trace_id)
        if not trace:
            continue
        spans = trace["spans"]
        summaries.append(
            {
                "trace_id": trace_id,
                "surface": trace["surface"],
                "started_at": trace["started_at"],
                "duration_ms": trace["duration_ms"],
                "outcome": trace["outcome"],
                "span_count": len(spans),
                "proof_areas": sorted({item["proof_area"] for item in spans}),
                "components": sorted({item["component"] for item in spans}),
                "edges": sorted(
                    {item["edge_id"] for item in spans if item.get("edge_id")}
                ),
            }
        )
        if len(summaries) == 16:
            break
    return summaries


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event(kind: str, label: str, **detail: Any) -> None:
    _EVENTS.appendleft(
        {"at": _iso_now(), "kind": kind, "label": label, **detail}
    )


def _safe_remote(remote: str | None) -> str:
    if not remote:
        return "unknown"
    if ":" in remote:
        groups = remote.split(":")
        return ":".join(groups[:2]) + ":…"
    octets = remote.split(".")
    return ".".join(octets[:3] + ["x"]) if len(octets) == 4 else remote


def heartbeat(
    client_id: str,
    surface: str,
    remote: str | None,
    user_agent: str,
    connected: bool = True,
) -> None:
    now = time.monotonic()
    short_id = client_id[:12]
    with _LOCK:
        previous = _CLIENTS.get(client_id)
        if not connected:
            if previous:
                _CLIENTS.pop(client_id, None)
                _event("client", "Client disconnected", client_id=short_id, surface=surface)
            return
        _CLIENTS[client_id] = {
            "client_id": short_id,
            "surface": surface[:40],
            "remote": _safe_remote(remote),
            "user_agent": user_agent[:140],
            "connected_at": previous["connected_at"] if previous else _iso_now(),
            "last_seen_monotonic": now,
            "last_seen": _iso_now(),
        }
        if previous is None:
            _event("client", "Client connected", client_id=short_id, surface=surface[:40])


def request_finished(path: str, status: int, duration_ms: float) -> None:
    if path.startswith("/api/calls"):
        group = "/api/calls"
    elif path.startswith("/api/clinic/patients/"):
        group = "/api/clinic/patients/:id"
    elif path.startswith("/api/residents/"):
        group = "/api/residents/:id"
    else:
        group = path
    with _LOCK:
        _REQUESTS["total"] += 1
        _REQUESTS[f"status_{status // 100}xx"] += 1
        _REQUESTS[group] += 1
        _LATENCY_MS["http"].append(duration_ms)


def workload_started(kind: str, label: str, detail: str = "") -> str:
    workload_id = uuid.uuid4().hex[:12]
    component, operation, edge_id = {
        "nemotron": ("nemotron", "nemotron.generate", "anchor-nemotron"),
        "csm": ("sesame-csm", "csm.synthesize", "anchor-csm"),
        "stt": ("whisper", "whisper.transcribe", "anchor-whisper"),
    }.get(kind, ("anchor-api", f"{kind}.execute", None))
    trace_span = _start_span(
        operation,
        component,
        "local-compute",
        edge_id,
        {"correlation": "GB10 machine sample; not exclusive attribution"},
    )
    with _LOCK:
        _WORKLOADS[workload_id] = {
            "workload_id": workload_id,
            "kind": kind,
            "label": label,
            "detail": detail[:120],
            "started_at": _iso_now(),
            "started_monotonic": time.monotonic(),
        }
        if trace_span:
            _WORKLOAD_SPANS[workload_id] = trace_span
        _event("workload", f"{label} started", workload_id=workload_id, engine=kind)
    return workload_id


def workload_finished(workload_id: str, outcome: str = "complete") -> None:
    gpu = gpu_sample()
    with _LOCK:
        workload = _WORKLOADS.pop(workload_id, None)
        if not workload:
            return
        duration_ms = (time.monotonic() - workload["started_monotonic"]) * 1000
        _LATENCY_MS.setdefault(workload["kind"], deque(maxlen=60)).append(duration_ms)
        _event(
            "workload",
            f"{workload['label']} {outcome}",
            workload_id=workload_id,
            engine=workload["kind"],
            duration_ms=round(duration_ms, 1),
        )
        trace_span = _WORKLOAD_SPANS.pop(workload_id, None)
    if trace_span:
        _finish_span(
            *trace_span,
            outcome,
            {
                "sampled_at": gpu.get("sampled_at"),
                "utilization_gpu": gpu.get("utilization_gpu"),
                "power_draw_w": gpu.get("power_draw_w"),
                "clock_sm_mhz": gpu.get("clock_sm_mhz"),
            },
        )


def _number(value: str) -> float | None:
    value = value.strip()
    if value in {"", "N/A", "[Not Supported]", "Not Supported"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def gpu_sample() -> dict[str, Any]:
    global _GPU_CACHE, _GPU_SAMPLED_MONOTONIC
    with _LOCK:
        if _GPU_CACHE is not None and time.monotonic() - _GPU_SAMPLED_MONOTONIC < 0.8:
            return dict(_GPU_CACHE)
    fields = (
        "name,uuid,utilization.gpu,utilization.memory,memory.used,memory.total,"
        "temperature.gpu,power.draw,power.limit,clocks.sm,clocks.mem"
    )
    try:
        result = subprocess.run(
            ["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        row = next(line for line in result.stdout.splitlines() if line.strip())
        values = [item.strip() for item in row.split(",")]
        if len(values) != 11:
            raise ValueError("unexpected nvidia-smi field count")
        sample = {
            "ready": True,
            "name": values[0],
            "uuid": values[1],
            "utilization_gpu": _number(values[2]),
            "utilization_memory": _number(values[3]),
            "memory_used_mib": _number(values[4]),
            "memory_total_mib": _number(values[5]),
            "temperature_c": _number(values[6]),
            "power_draw_w": _number(values[7]),
            "power_limit_w": _number(values[8]),
            "clock_sm_mhz": _number(values[9]),
            "clock_memory_mhz": _number(values[10]),
            "sampled_at": _iso_now(),
        }
    except (FileNotFoundError, subprocess.SubprocessError, StopIteration, ValueError) as exc:
        sample = {
            "ready": False,
            "error": type(exc).__name__,
            "sampled_at": _iso_now(),
        }
    with _LOCK:
        _GPU_CACHE = sample
        _GPU_SAMPLED_MONOTONIC = time.monotonic()
    return dict(sample)


def _average(values: deque[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def snapshot() -> dict[str, Any]:
    gpu = gpu_sample()
    cutoff = time.monotonic() - CLIENT_TTL_SECONDS
    with _LOCK:
        expired = [key for key, client in _CLIENTS.items() if client["last_seen_monotonic"] < cutoff]
        for key in expired:
            client = _CLIENTS.pop(key)
            _event("client", "Client timed out", client_id=client["client_id"], surface=client["surface"])
        clients = []
        for client in _CLIENTS.values():
            public = {key: value for key, value in client.items() if key != "last_seen_monotonic"}
            public["age_seconds"] = round(time.monotonic() - client["last_seen_monotonic"], 1)
            clients.append(public)
        workloads = []
        for workload in _WORKLOADS.values():
            public = {key: value for key, value in workload.items() if key != "started_monotonic"}
            public["elapsed_ms"] = round((time.monotonic() - workload["started_monotonic"]) * 1000, 1)
            workloads.append(public)
        return {
            "sampled_at": _iso_now(),
            "uptime_seconds": round(time.monotonic() - STARTED_AT),
            "gpu": gpu,
            "clients": sorted(clients, key=lambda item: item["connected_at"]),
            "active_client_count": len(clients),
            "workloads": sorted(workloads, key=lambda item: item["started_at"]),
            "request_counts": dict(_REQUESTS),
            "average_latency_ms": {key: _average(values) for key, values in _LATENCY_MS.items()},
            "events": list(_EVENTS)[:30],
            "traces": _trace_summaries(),
            "trace_buffer": {"count": len(_TRACES), "limit": _TRACE_LIMIT},
        }
