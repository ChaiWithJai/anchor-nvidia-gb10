"""Regression tests over the labelled sets.

These lock in what classify_utterance() currently does, so a change to the
term lists cannot silently move the numbers. They are deliberately asserted as
exact figures rather than thresholds -- if one moves, that should be a
conscious decision recorded in the diff, not a passing build.

Note what the corpus number is NOT: roughly 41% of each tier-3 transcript is
verbatim from the phrase list circulated while the corpus was scripted, so
150/150 measures whether the lists detect the vocabulary they encode. The
holdout is the honest generalisation figure.
"""
import json
import os
import re

import pytest

EVAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eval")


def _call_tier(escalation, text):
    """Whole-call tier: the max across turns, as check_and_alert ratchets."""
    tier = 1
    turns = [t.strip() for t in re.split(r"(?<=[.!?])\s+", text) if t.strip()] or [text]
    for turn in turns:
        tier = max(tier, escalation.classify_utterance(turn)["triage_tier"])
    return tier


def _score(escalation, filename):
    data = json.load(open(os.path.join(EVAL, filename)))
    rows = [(d["tier"], _call_tier(escalation, d["text"])) for d in data]
    return {
        "n": len(rows),
        "correct": sum(1 for a, b in rows if a == b),
        "tier3_total": sum(1 for a, _ in rows if a == 3),
        "tier3_recall": sum(1 for a, b in rows if a == 3 and b == 3),
        "under": sum(1 for a, b in rows if b < a),
        "over": sum(1 for a, b in rows if b > a),
    }


def test_corpus150_conformance(escalation):
    """The scripted corpus. Perfect by construction -- see the module docstring."""
    r = _score(escalation, "corpus150.json")
    assert r["n"] == 150
    assert r["correct"] == 150
    assert r["tier3_recall"] == 50
    assert r["over"] == 0, "a false positive on a tier-1 call is the demo-breaking error"


def test_holdout_is_the_honest_number(escalation):
    """Blind holdout: written to the clinical rubric, never used to build a list.

    If this ever reaches 12/12 by list changes alone, be suspicious -- it most
    likely means the holdout phrasings were added to the lists, which measures
    nothing about the next caller.
    """
    r = _score(escalation, "holdout.json")
    assert r["n"] == 12
    assert r["correct"] == 8, "term lists alone: 67%"
    assert r["tier3_recall"] == 2, "2 of 4 at-risk callers are missed without the model"
    assert r["over"] == 0


def test_no_false_positives_on_low_risk_language(escalation):
    """Illness and planned-exit language must stay tier 1.

    These read as risky to a naive matcher and are the errors that erode trust
    in every other alert.
    """
    for text in [
        "I have had a rotten flu and been in bed two days with a fever",
        "I drove myself so I could leave early and ordered a soda at the bar",
        "There was wine on the table and I noticed it but it did not really pull at me",
        "The urge was manageable and passed after about twenty minutes",
    ]:
        assert _call_tier(escalation, text) == 1, f"false positive on: {text!r}"


@pytest.mark.parametrize("text", [
    "everyone would have an easier time without me",
    "I counted them and I know the number",
])
def test_known_crisis_language_fires(escalation, text):
    assert _call_tier(escalation, text) == 3, f"crisis floor missed: {text!r}"


# --------------------------------------------------------------------- #
# Contraction folding. Speech recognition emits "do not" / "cannot" /
# "was not"; the term list is written with contractions. Without folding,
# 13 of 51 CRISIS_TERMS could never fire on real ASR output -- including
# passive-ideation and cannot-keep-safe language.
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("asr_text,contraction", [
    ("I wish I was not here", "wish i wasn't here"),
    ("I do not want to wake up", "don't want to wake up"),
    ("I cannot keep myself safe", "can't keep myself safe"),
    ("I am not safe on my own", "i'm not safe on my own"),
    ("I am a burden to everyone", "i'm a burden"),
    ("I cannot feel my way out", "can't feel my way out"),
])
def test_expanded_asr_forms_reach_the_crisis_floor(escalation, asr_text, contraction):
    assert _call_tier(escalation, asr_text) == 3, (
        f"ASR emits {asr_text!r} but the list only had {contraction!r}")


def test_every_crisis_term_still_matches_itself(escalation):
    """Folding must not break a single existing term."""
    missed = [t for t in escalation.CRISIS_TERMS
              if escalation.classify_utterance(t)["triage_tier"] != 3]
    assert missed == [], f"folding broke these terms: {missed}"


def test_folding_is_idempotent(escalation):
    once = escalation.fold_contractions("I can't and I cannot and I do not")
    assert escalation.fold_contractions(once) == once


def test_crisis_floor_gap_still_open(escalation):
    """One phrasing the list still misses, a preposition from one it has.

    Asserting CURRENT behaviour so the gap lives in the suite rather than in
    folklore. Flip to == 3 when "trust myself" is added to CRISIS_TERMS.
    """
    assert _call_tier(escalation, "I do not trust myself to keep myself safe") == 1
