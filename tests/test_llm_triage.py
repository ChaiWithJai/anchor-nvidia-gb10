"""Tests for the Nemotron triage layer.

Every claim the PR makes about this layer is asserted here. The two that
matter most are the invariants: the model may only RAISE a tier, and a
classifier failure must never be reported as a tier-3 finding about the
patient.
"""
import asyncio

import pytest


# --------------------------------------------------------------------- #
# message_text: the parser bug that failed 11 of 12 live calls on the GB10.
# vLLM with --reasoning-parser nemotron_v3 leaves content null and puts the
# text in reasoning_content.
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("message,expected", [
    ({"content": '{"tier": 3}'}, '{"tier": 3}'),
    ({"content": None, "reasoning_content": '{"tier": 2}'}, '{"tier": 2}'),
    ({"content": [{"type": "text", "text": '{"tier": 1}'}]}, '{"tier": 1}'),
    ({"content": "", "reasoning_content": "  ", "text": '{"tier": 3}'}, '{"tier": 3}'),
])
def test_message_text_handles_every_shape(triage_module, message, expected):
    assert triage_module.message_text(message).strip() == expected


def test_message_text_returns_empty_when_there_is_nothing(triage_module):
    assert triage_module.message_text({"content": None, "reasoning_content": None}) == ""
    assert triage_module.message_text({}) == ""


# --------------------------------------------------------------------- #
# triage(): every failure path reports ok=False and never invents a tier.
# --------------------------------------------------------------------- #

def _fake_post(payload=None, exc=None):
    class _Response:
        def raise_for_status(self): pass
        def json(self): return payload

    class _Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, *a, **k):
            if exc:
                raise exc
            return _Response()

    return lambda *a, **k: _Client()


def test_triage_parses_a_good_response(triage_module, monkeypatch):
    monkeypatch.setattr(triage_module.httpx, "AsyncClient", _fake_post(
        {"choices": [{"message": {"content":
            '{"tier": 3, "category": "ideation", "rationale": "said they cannot stay safe"}'}}]}))
    tier, why, ok = asyncio.run(triage_module.triage("some text"))
    assert (tier, ok) == (3, True)
    assert "cannot stay safe" in why


def test_triage_reads_reasoning_content(triage_module, monkeypatch):
    """The exact shape the GB10 served, which used to fail."""
    monkeypatch.setattr(triage_module.httpx, "AsyncClient", _fake_post(
        {"choices": [{"message": {"content": None,
                                  "reasoning_content": '{"tier": 2, "rationale": "recurring"}'}}]}))
    tier, _, ok = asyncio.run(triage_module.triage("some text"))
    assert (tier, ok) == (2, True)


@pytest.mark.parametrize("payload,exc", [
    (None, ConnectionError("refused")),
    ({"choices": [{"message": {"content": None}}]}, None),
    ({"choices": [{"message": {"content": "I think this is tier three"}}]}, None),
    ({"choices": [{"message": {"content": '{"tier": 7}'}}]}, None),
    ({"choices": [{"message": {"content": '{"tier": "three"}'}}]}, None),
    ({}, None),
])
def test_triage_never_invents_a_tier_on_failure(triage_module, monkeypatch, payload, exc):
    monkeypatch.setattr(triage_module.httpx, "AsyncClient", _fake_post(payload, exc))
    tier, why, ok = asyncio.run(triage_module.triage("some text"))
    assert ok is False
    assert tier is None, "a failed classifier must not produce a tier"
    assert why


# --------------------------------------------------------------------- #
# should_run: cost and risk gating.
# --------------------------------------------------------------------- #

def test_should_run_skips_tier_3_and_short_turns(triage_module):
    long_text = "x" * 200
    assert triage_module.should_run(long_text, 1) is True
    assert triage_module.should_run(long_text, 3) is False, "tier 3 needs no model"
    assert triage_module.should_run("yeah", 1) is False, "too short to judge"
    triage_module.ENABLED = False
    assert triage_module.should_run(long_text, 1) is False
    triage_module.ENABLED = True


# --------------------------------------------------------------------- #
# INVARIANT 1 — the model may only raise a tier.
# A hallucination that could lower one turns a model error into a missed
# at-risk caller.
# --------------------------------------------------------------------- #

def _apply(escalation, triage_module, text, tier_returned, ok=True, call_id="c1"):
    async def fake(_text):
        return tier_returned, "because", ok
    triage_module.triage = fake
    classification = escalation.classify_utterance(text)
    result = asyncio.run(
        escalation._apply_llm_triage("patient-01", call_id, text, classification))
    return classification, result


@pytest.mark.parametrize("model_tier", [1, 2])
def test_model_cannot_lower_a_tier(escalation, triage_module, model_tier):
    text = "I have counted them and I do not feel safe on my own tonight at all"
    before, after = _apply(escalation, triage_module, text, model_tier)
    assert after["triage_tier"] >= before["triage_tier"]


def test_model_raises_what_the_term_lists_miss(escalation, triage_module):
    """The holdout caller both term lists miss."""
    text = "the maths works out better for everyone if I am not in it any more"
    before, after = _apply(escalation, triage_module, text, 3)
    assert before["triage_tier"] < 3, "precondition: the lists do not catch this"
    assert after["triage_tier"] == 3
    assert after["false_positive_trap"] is False


def test_raising_to_tier_3_produces_a_crisis_score(escalation, triage_module):
    """check_and_alert derives crisis from score == 10; a raise must set it."""
    text = "the maths works out better for everyone if I am not in it any more"
    _, after = _apply(escalation, triage_module, text, 3)
    assert after["score"] == 10


# --------------------------------------------------------------------- #
# INVARIANT 2 — a failure is an operational fault, not a clinical finding.
# Returning tier 3 on a timeout labels the patient's own words critical
# because inference broke. That produced 7 over-alerts in 12 calls.
# --------------------------------------------------------------------- #

BENIGN = "Today was ordinary, work was fine and I met my sister for dinner afterwards."


def test_outage_does_not_escalate_a_benign_turn(escalation, triage_module, stubs):
    before, after = _apply(escalation, triage_module, BENIGN, None, ok=False)
    assert after["triage_tier"] == before["triage_tier"]
    assert after["triage_tier"] != 3, "an outage must not mark the patient critical"


def test_outage_raises_exactly_one_ops_alert_per_call(escalation, triage_module, stubs):
    _apply(escalation, triage_module, BENIGN, None, ok=False, call_id="call-x")
    _apply(escalation, triage_module, BENIGN, None, ok=False, call_id="call-x")
    faults = [a for a in stubs if a["alert_type"] == "classifier-unavailable"]
    assert len(faults) == 1, "one operational alert per call, not per turn"
    assert faults[0]["severity"] == "medium"
    assert faults[0]["tier"] != 3, "the ops alert carries the lists' tier, not a fabricated 3"


def test_outage_still_lets_the_term_lists_escalate(escalation, triage_module, stubs):
    """The deterministic floor must survive the model being down."""
    text = "I have counted them twice this week"
    before, after = _apply(escalation, triage_module, text, None, ok=False, call_id="call-y")
    assert after["triage_tier"] == before["triage_tier"]
