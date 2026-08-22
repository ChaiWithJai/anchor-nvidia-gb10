# Tests

    python3 -m pytest tests/ -q          # 35 tests, no GPU, no MongoDB, no vLLM

`conftest.py` stubs `memory` and `agent_wake`, so the triage logic runs without
any infrastructure. Note that `escalation.py` binds those at import time, so the
fixture patches the module attributes rather than `sys.modules` alone.

**test_llm_triage.py** — the Nemotron layer. Asserts the two invariants the
design rests on: the model may only RAISE a tier, and a classifier failure is
an operational fault that never becomes a tier-3 finding about the patient.
Also covers every response shape `message_text()` must survive, including the
`reasoning_content` case that failed 11 of 12 live calls on the GB10.

**test_classification_regression.py** — locks in the numbers over both labelled
sets, as exact figures rather than thresholds: if one moves, it should be a
conscious decision visible in the diff. Includes the contraction-folding cases
and one documented, still-open gap in `CRISIS_TERMS`.
