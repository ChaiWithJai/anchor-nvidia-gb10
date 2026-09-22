# Phase two: implement MLflow evaluation-driven development for Nemotron and Bonsai on GB10

## Outcome

Build a reproducible process that turns Anchor events and conversations into reviewed datasets, compares Nemotron with Bonsai, and connects model changes to deployment and observed behavior. Demonstrate reduced total memory while preserving predefined task quality, then show a useful additional clinical operations workload within the released capacity.

The canonical design is [Phase two: evaluation-driven development](../phase-two-evaluation.md). The baseline is the existing Nemotron 30B NVFP4 application, and the first proposed candidate is Ternary Bonsai 2 27B, subject to an exact checkpoint/runtime verification. No benchmark result or universal losslessness claim is implied by opening this issue.

## Official references

- [MLflow end-to-end evaluation-driven development](https://mlflow.org/docs/latest/genai/datasets/end-to-end-workflow/) describes tracing, trace collection, expectations, datasets, evaluation, and iteration.
- [MLflow feedback](https://mlflow.org/docs/latest/genai/assessments/feedback/) distinguishes output assessments from expected behavior.
- [MLflow regression testing](https://mlflow.org/docs/latest/genai/eval-monitor/regression-testing/) connects agent behavior to CI.
- [MLflow automatic evaluation](https://mlflow.org/docs/latest/genai/eval-monitor/automatic-evaluations/) documents monitoring, session evaluation, and judge prerequisites.

Anchor organizes the work as data/annotation, optimization/training, deployment, and observation. That grouping is our lifecycle, not a claim that MLflow mandates four steps or that all training is reinforcement learning.

## Dependencies and scope

Phase one must finish before measured comparisons. Downloads and documentation work may run in parallel, but GPU evaluation must use an exclusive measurement window. Use the existing FastAPI, MongoDB, safety handlers, WebSocket endpoint, and MLflow server. Preserve the current architecture and avoid a second model-serving stack competing for the same GB10.

Use synthetic, non-identifying data for the proof of concept. EHR integration is a proposed reviewed clinical-operations extension, not an existing clinical deployment. The issue does not authorize autonomous care-plan changes, patient contact, or production EHR writeback.

## Setup already completed

- [x] Confirmed the existing MLflow 3.16.0 server with SQLite backend on GB10 loopback port 5210.
- [x] Created `Anchor Phase Two Evaluation` (experiment 14), separate from deployment experiment 13.
- [x] Created empty candidate, development, holdout, and production-replay datasets with synthetic/approved-data policy and awaiting-review tags.
- [x] Added idempotent setup in `scripts/bootstrap-phase-two.py`.

The candidate dataset now contains one observed synthetic call, marked unreviewed, from the live WebSocket verification. The other datasets remain empty, and no reviewed labels or scores have been fabricated. Training and judge-calibration splits still need explicit setup when required. Functional baseline verification passed; the first observed summary-grounding failure is tracked in [issue #24](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/24).

## Workstream 0: preserve and prove the baseline

- [ ] Record the application commit, image digest, model revision/checksums, launch configuration, host/driver/runtime versions, and MongoDB schema version.
- [x] Link real readiness, synthetic WebSocket conversation, transcript readback, and safety/handoff-status verification. MLflow experiment 13 runs: readiness `309610c1f9c74510a2f268818b9cef11`, full workload `52ac3bab3d374ec4937267cdf6e11906`, WebSocket `fce23d52566a4d34be525de34adbc0cf`. Optional OpenClaw delivery remains unconfigured.
- [ ] Record current memory pressure and all resident services, including voice and speech recognition.
- [ ] Save a rollback manifest and verify that it restores the baseline without deleting MongoDB data.
- [ ] Confirm the exact Bonsai artifact, license, format, tokenizer/template, runtime, context limits, and GB10 support.

Acceptance: another operator can reproduce the verified baseline and identify each installed artifact. A container that started without successful inference does not count as ready.

## Workstream 1: establish the MLflow evidence contract

- [ ] Inventory the existing server/client versions, backend type, artifact store, access boundary, and existing Anchor experiment.
- [ ] Verify SQL-backed Evaluation Datasets support using a synthetic record. Pin compatible dependencies; document any feature unavailable locally.
- [ ] Define run kinds for deployment, trace capture, annotation export, dataset release, generation/training, evaluation, capacity, cost, and promotion.
- [ ] Establish parent/child or explicit linked runs and tags for phase, candidate, commit, dataset digest, and workstream.
- [ ] Capture durable application spans and session IDs without inserting a blocking MLflow dependency into each patient turn.
- [ ] Document redaction, retention, telemetry errors, and restricted artifacts. Never log private voice references or identifying records to public artifacts.
- [ ] Add a manifest validator that rejects missing model, dataset, scorer, or code references in a reportable evaluation run.

Acceptance: a synthetic source event can be followed through its trace, annotation, dataset snapshot, evaluation result, and deployment reference. The current process-command trace is not mistaken for complete application observability.

## Workstream 2: collect, review, and version data

- [ ] Inventory available approved traces and inspect representative complete records before deciding whether generation is needed.
- [ ] Define workflow, risk/ambiguity, and context-condition dimensions tied to plausible failures.
- [ ] If traces are scarce, draft about 20 scenario tuples for domain review. Generate wording separately only after the tuples are reviewed.
- [ ] Run a discovery batch through the whole application and retain intermediate context, model calls, safety decisions, persistence, and errors.
- [ ] Support human free-text review of complete traces and cluster observations into a failure taxonomy.
- [ ] Define expectations and feedback separately, including evidence spans, reviewer provenance, uncertainty, and adjudication.
- [ ] Specify a clinical reviewer for care-boundary expectations and label unreviewed generated expectations explicitly.
- [ ] Create training, development, judge-calibration, and held-out test splits grouped by patient/session/scenario family.
- [ ] Check exact and near duplicates and keep generated descendants with their source split.
- [ ] Export immutable snapshots with SHA-256, split assignments, schema, source IDs, and inclusion/exclusion decisions.

Acceptance: all evaluation rows have source lineage and reviewed expectations appropriate to their use. A human can reproduce the split. No optimization process consumes the held-out test answers.

## Workstream 3: implement scorers and calibrate judgment

- [ ] Add deterministic checks for persisted safety alerts, authored high-risk responses, actual handoff status, plan authority, consent, isolation, and input constraints.
- [ ] Evaluate plan adherence, supported facts, memory fidelity, summary attribution, missing/conflicting context, and appropriate handling of uncertainty.
- [ ] Cover ordered WebSocket turns, reconnect, malformed messages, completion, access controls, and transcript equivalence with the existing HTTP workflow.
- [ ] Include a retrieval counterfactual and report turns where deterministic responses bypass the model.
- [ ] Define a rubric from reviewed failures rather than a generic overall helpfulness score.
- [ ] Calibrate any LLM judge against independent adjudicated human labels, reporting class-specific errors and disagreement.
- [ ] Blind candidate identity, randomize comparison order, and log judge model, prompt, settings, code, and cost.
- [ ] Distinguish missing, failed, skipped, and passed assessments.

Acceptance: all critical checks have interpretable per-case evidence. Judge quality is measured before aggregate judge scores can support promotion. A code check is used where a deterministic property is sufficient.

## Workstream 4: compare unchanged models first

- [ ] Freeze prompts, retrieval snapshot, cases, application revision, output budget, and benchmark procedure.
- [ ] Run Nemotron and each Bonsai candidate sequentially on the same GB10, recording model-specific templates or unavoidable runtime differences.
- [ ] Measure cold-start and warmed runs separately; repeat when variability affects conclusions.
- [ ] Record whole-stack memory, peak pressure, swap, model load time, time to first token, token rate, p50/p95 turn latency, completion/error rates, and power with measurement scope.
- [ ] Capture paired quality differences and confidence intervals grouped by session/scenario family.
- [ ] Declare the primary outcome, non-inferiority margin, sample size, slice requirements, concurrency, and performance budgets before candidate results are examined.
- [ ] Publish baseline/candidate run IDs, artifacts, per-case results, resource traces, exclusions, and limitations.

Acceptance: candidate conclusions distinguish measured improvement, inconclusive evidence, and regression. No deployment proceeds on a favorable mean while critical cases fail. Model/runtime comparisons do not claim to isolate precision alone.

## Workstream 5: optimize only from observed failures

- [ ] Record a hypothesis, intervention, expected effect, control, and decision rule for every optimization run.
- [ ] Evaluate prompt/context fixes before assuming weight training is needed.
- [ ] For distillation, track teacher provenance, generation terms, filtering, human review, and student parent checkpoint.
- [ ] For supervised fine-tuning, record data digest, adapters/full weights, optimizer, seeds, trainable parameters, and output hashes.
- [ ] For quantization/pruning, establish representation/runtime compatibility and paired controls where possible. Measure actual allocated memory and kernel performance.
- [ ] For preference optimization or RL, specify reward/preferences, rollout policy if applicable, optimizer, held-out reward validation, and reward-exploitation tests.
- [ ] Rerun development/regression cases and the critical safety suite after each proposed release candidate. Reserve the final holdout for a predeclared promotion decision, record each exposure, and create a new holdout if its failures guide further optimization.
- [ ] Record compute, generation, annotation, and engineering cost for the local synthetic-data loop.

Acceptance: each optimized artifact has a reproducible parent and data lineage. Feedback logging is never labeled as completed RL, and local inference is never reported as zero total cost.

## Workstream 6: demonstrate the released capacity

- [ ] Select one additional clinical operations workload, starting with a draft summary of logged activities with source references.
- [ ] Define its input contract, expected output, human review step, and synthetic EHR mapping fixtures.
- [ ] Benchmark the workload alone and co-resident with the full voice/text Anchor stack.
- [ ] Check interference with tail latency, safety persistence, memory pressure, and completion rates.
- [ ] Document actual sustainable concurrency and failure recovery rather than extrapolating from free memory alone.

Acceptance: the added workload completes under agreed budgets on the same machine. All outputs remain drafts for review, and EHR writes remain a separate integration decision.

## Workstream 7: deployment, observation, and regression

- [ ] Promote a complete application/model/prompt/configuration manifest tied to passing evaluation evidence.
- [ ] Use synthetic or shadow traffic first and rehearse rollback to Nemotron.
- [ ] Monitor quality findings, errors, latency, memory pressure, escalation/handoff failures, and reviewer corrections by slice.
- [ ] Budget monitoring/judge sampling independently of serving and record missing telemetry.
- [ ] Verify installed support before enabling MLflow automatic evaluation. Its documented gateway/judge requirements must not silently introduce a new serving dependency.
- [ ] Run code-based regression checks in tests or the evaluation runner; use automatic evaluation only for supported judge types.
- [ ] Turn reviewed production failures into new regression cases and a versioned dataset release.
- [ ] Link incidents to deployment, trace, issue, fix, and re-evaluation.

Acceptance: the team can explain which release produced an observed failure, how the failure was reviewed, and which evaluation proves the fix. Telemetry failure must not stop care-serving behavior.

## Workstream 8: cost analysis dependency

- [x] Create and link [cost and capacity issue #22](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/22) and the [initial scenario report](../phase-two-cost-analysis.md).
- [ ] Combine measured local inference/resources with hardware, electricity, maintenance, annotation, evaluation, and operations assumptions.
- [ ] Compare current provider scenarios with the same workload volume, token distribution, context, retries, voice, concurrency, and availability assumptions.
- [ ] Separate token charges from contracted requirements, retention, support, security operations, EHR integration, and other HIPAA-related deployment costs.
- [ ] Identify whether vendor pricing, service eligibility, and contract assumptions are verified, quoted, estimated, or unavailable.
- [ ] Show low/base/high monthly bills and sensitivity/break-even calculations. Do not claim a provider is suitable from list pricing alone.

Acceptance: the opportunity estimate is reproducible and labels measured values, assumptions, and unavailable quotes. No invented discount, BAA price, or unverified clinical-compliance claim enters the report.

## Definition of done

- [x] Phase-one functional startup is proven with linked MLflow evidence. Clinical quality remains an evaluation requirement, including issue #24.
- [ ] A reviewed, versioned dataset and calibrated evaluation process exist.
- [ ] Nemotron and at least one compatible Bonsai candidate have reproducible comparisons.
- [ ] The proposed candidate passes all critical deterministic cases and predeclared quality/performance gates, or the documented result explicitly rejects/inconclusively evaluates it.
- [ ] A capacity experiment and cost report show the practical consequence of the result.
- [ ] Deployment/rollback and observation procedures are exercised for any promoted candidate.
- [ ] Repository documentation links source lineage, current decision, open gaps, and exact evidence without asserting unmeasured results.

## Decisions to record before execution

Assign the engineering owner, clinical reviewer, dataset owner, and release decision owner. Resolve the exact Bonsai artifact/runtime, permissible data sources, primary task, clinical quality margin, sample size, concurrency, latency/memory budgets, and retention. Track unresolved decisions as explicit blockers to the affected workstream, while independent synthetic setup and documentation continue.
