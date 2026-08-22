"""Test fixtures. Stubs the persistence and OpenClaw hand-off so the triage
logic can be exercised without MongoDB, vLLM, or a GB10."""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))

import pytest


@pytest.fixture
def stubs(monkeypatch):
    """Install stub memory + agent_wake modules and return the alert log."""
    saved = []

    memory = types.ModuleType("careline.memory")

    def save_alert(resident_id, call_id, reason, severity,
                   alert_type="safety-escalation", tier=None, pattern_key=None):
        saved.append({"resident_id": resident_id, "call_id": call_id,
                      "reason": reason, "severity": severity,
                      "alert_type": alert_type, "tier": tier})
        return f"alert-{len(saved)}"

    memory.save_alert = save_alert
    memory.set_alert_delivery = lambda *a, **k: None
    memory.goal_miss_patterns = lambda resident_id: []
    memory.list_alerts = lambda **k: []

    agent_wake = types.ModuleType("careline.agent_wake")

    async def notify(alert):
        return {"status": "delivered", "target": "OpenClaw"}

    agent_wake.notify = notify
    agent_wake.status = lambda: {"configured": True, "name": "OpenClaw"}

    monkeypatch.setitem(sys.modules, "careline.memory", memory)
    monkeypatch.setitem(sys.modules, "careline.agent_wake", agent_wake)

    # escalation.py binds these at import time (`from . import memory`), so
    # replacing sys.modules alone is too late once it has been imported.
    from careline import escalation
    monkeypatch.setattr(escalation, "memory", memory, raising=False)
    monkeypatch.setattr(escalation, "agent_wake", agent_wake, raising=False)
    return saved


@pytest.fixture
def escalation(stubs):
    from careline import escalation as module
    module._TRIAGE_DEGRADED.clear()
    return module


@pytest.fixture
def triage_module():
    from careline import llm_triage as module
    module.ENABLED = True
    return module
