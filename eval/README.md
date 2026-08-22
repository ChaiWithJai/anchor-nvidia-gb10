# Severity classification — corpus, holdout, harness

    corpus.json         15 clinician-labelled calls (5 per tier). The lexicon
                        was fitted from these, so scores here are IN-SAMPLE.
    holdout.json        12 calls written to a clinical rubric and never shown
                        to the fitter. This is the honest number.
    coverage_gaps.json  risk presentations named in the rubric that appear
                        NOWHERE in the corpus. The recording brief.

## Run it

    PYTHONPATH=app python3 tools/evaluate.py eval/holdout.json --llm

Scores the lexicon, Nemotron and combined separately.

Exit codes: `0` every call classified and no at-risk misses · `1` at-risk miss
or any classifier failure · `2` every classifier call failed, no score possible.

**Failed classifier calls are excluded from the matrices and force a non-zero
exit.** An earlier version scored a failure as a tier-3 prediction, so a run
where 11 of 12 calls failed reported perfect tier-3 recall and exited 0. A gate
that passes while the classifier is broken is worse than no gate.

## What the numbers say

| | corpus (in-sample) | holdout (blind) |
|---|---|---|
| previous 8 patterns | **0/15** | — |
| lexicon, fitted from corpus only | 15/15 | 33%, **0/4 tier-3** |
| \+ clinical risk categories | 15/15 | 75%, **2/4 tier-3** |
| \+ Nemotron | — | **not yet measured** |

Adding documented risk language (passive ideation, burdensomeness, means at
hand) more than doubled blind accuracy and cost nothing in-sample — no
regression, no over-alerts. It is worth having.

It is still not a predictor. Two holdout callers describing wanting to die get
no alert, and the reasons are one word each:

- "a weight on **that** family" — the pattern lists `this|my|the`
- "if I'm not in it" — the pattern wants `without me in it`
- the coping tool "gone flat on me" — the pattern has `stopped working`
- one refusal cue where the override needs two

The phrase list and this holdout were written by the same author, sharing
vocabulary. With every advantage, the lexicon still misses two at-risk callers.
A real caller phrasing it their own way will do worse. Extending the list until
these four pass would make the number green and teach us nothing about the
fifth caller — that is why the list stops here and Nemotron runs.

The lexicon on its own scores the same as always answering "tier 1", because
unmatched text falls through to the tier-1 default. It works on phrasing it has
seen. It is a fast floor and a fallback, **not** the classifier — Nemotron is.

The Nemotron path has never made a real inference call. It has only been
exercised against a stub and a dead endpoint (to prove it fails safe). The
first genuine test is the command above, on the GB10.

## Regenerating

    python3 tools/transcribe.py    # wav -> transcripts (needs the audio archive)
    python3 tools/fit_lexicon.py   # refits weights, writes a new INACTIVE version

Fitting never touches the crisis floor. New lexicon versions are inactive until
a human activates them.
