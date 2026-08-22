# Severity triage — corpus, holdout, harness

    corpus150.json      150 clinician-labelled calls, transcribed. Balanced
                        50/50/50 across tiers, 10 speakers.
    holdout.json        12 calls written to a clinical rubric, never used to
                        build any term list.
    coverage_gaps.json  risk presentations named in the rubric that appear in
                        no recording. The brief for the next corpus.

## Run it

    PYTHONPATH=app python3 tools/evaluate.py eval/holdout.json --llm

Scores `classify_utterance()`, Nemotron, and combined separately.

Exit codes: `0` everything classified, no at-risk misses · `1` an at-risk miss
or any classifier failure · `2` every classifier call failed.

Failed classifier calls are excluded from the matrices and force a non-zero
exit. Scoring a failure as a tier-3 prediction makes a broken classifier report
perfect recall — a gate that passes while the classifier is down is worse than
no gate.

## Numbers

| | corpus150 | holdout (blind) |
|---|---|---|
| `classify_utterance()` alone | 150/150, tier-3 50/50 | **67%, tier-3 2/4** |
| \+ Nemotron | — | **not yet measured** |

**The corpus number is conformance, not accuracy.** Roughly 41% of each tier-3
transcript is verbatim from the phrase list circulated while the corpus was
being scripted, so it measures whether the term lists detect the vocabulary they
encode. They do, perfectly, with zero false positives across 50 tier-1 calls —
that is worth having and worth demoing.

The holdout is the honest figure. Two callers describing wanting to die get no
alert, over wording the lists do not contain:

    "the maths works out better for everyone if I'm not in it"
    "I've counted them twice this week and I don't like that I know the number"

Extending the lists until those pass would turn the number green and teach us
nothing about the next caller. That is what the Nemotron layer is for.

## Status of the Nemotron layer

**It has never successfully classified a call.** The only live attempt, on the
GB10, failed 11 of 12 calls because the response parser assumed
`message.content` is a string; vLLM with `--reasoning-parser nemotron_v3` puts
the text in `reasoning_content` and can leave `content` null. That parser is
fixed in `llm_triage.message_text()`, but the fix is unverified against the real
endpoint.

Until the command above returns a clean run, the shipped behaviour is term
lists only: 67% on unseen wording.
