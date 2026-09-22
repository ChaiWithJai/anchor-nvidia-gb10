# Measure Anchor phase-two cost, capacity and healthcare deployment economics

Published issue: [#22](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/22).

## Outcome

Produce an MLflow-backed comparison of local Nemotron and Bonsai that joins clinical workflow quality, memory, latency, power and fully allocated cost. Compare the accepted local configurations with eligible hosted inference alternatives using a reproducible monthly workload model. The final report must distinguish observed data, public pricing, contract quotes and planning assumptions.

The research baseline and initial arithmetic are in [phase-two-cost-analysis.md](../phase-two-cost-analysis.md). As of 2026-09-22, the planning case has 1,000 patients, eight five-minute check-ins each month, 96 million input tokens and 12 million output tokens. Public GPT-OSS 120B text rates at Groq, Together and Fireworks imply $21.60 monthly before audio and other application costs. That figure is a hypothetical inference invoice, not the total clinical service bill.

## Scope and dependencies

Parent: [Phase-two evaluation-driven development, issue #21](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/21).

- Complete baseline deployment and real application verification before performance trials.
- Use `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` and `prism-ml/Ternary-Bonsai-2-27B-gguf` / `Ternary-Bonsai-2-27B-PQ2_0` as distinct pinned local candidates.
- Preserve the existing application architecture, browser voice flow, websocket messaging, MongoDB persistence and deterministic safety actions.
- Depend on the phase-two dataset and annotation work for frozen evaluation rows, clinician expectations and held-out cases.
- Extend other Bonsai family members only when their model identity, runtime support and licenses have been verified.
- Use synthetic records during research. Do not send protected health information to public demo or uncontracted services.

## Work package 1: document the workload

- [ ] Define a completed and accepted check-in, with explicit quality and safety criteria.
- [ ] Record patients, check-ins, turns, context length, retries, cancellations and peak concurrency.
- [ ] Measure input, output and reasoning tokens per model tokenizer; separate cached tokens where billed differently.
- [ ] Record input audio seconds, synthesized audio seconds or characters, and any voice enrollment work.
- [ ] Add separate workload rows for activity extraction, summaries, embeddings, evaluation judges, synthetic generation, training and EHR transfers.
- [ ] Publish pilot, planning and larger-volume assumptions alongside recorded samples.
- [ ] Keep original audio retention policy explicit. Do not introduce recording storage merely to complete a cost worksheet.

## Work package 2: use the official MLflow cost workflow

Follow [MLflow token usage and cost tracking](https://mlflow.org/docs/latest/genai/tracing/token-usage-cost/). Inspect the installed server version and dependencies. Keep the existing tracking service and baseline history intact.

- [ ] Verify version 3.10 or newer and the server's `genai` extra before relying on cost charts.
- [ ] Trace LLM, STT, TTS, application, database and downstream calls under correlated request/session IDs.
- [ ] Populate custom endpoint usage with `mlflow.chat.tokenUsage` and explicitly documented estimated counts when no exact count exists.
- [ ] Populate applicable invoice costs through `mlflow.llm.cost`; test that unknown model prices remain visibly unknown rather than silently zero.
- [ ] Mark local external-token charges as known zero while retaining energy, equipment and staff costs in separate metrics.
- [ ] Store versioned price schedules, sources, effective dates, currency, model IDs, pricing mode and BAA status.
- [ ] Show span cost, trace total and experiment-level cost views. Verify aggregation against a small hand-calculated fixture with retries.
- [ ] Link evaluation row, human assessment, dataset version, prompt version, code commit and model revision to every compared result.
- [ ] Keep actual costs distinct from counterfactual hosted projections and amortized ownership costs.

## Work package 3: run matched local trials

- [ ] Freeze prompts and datasets before candidate comparison. Register a numeric non-inferiority margin and latency targets with clinical reviewers.
- [ ] Pin model artifact hashes, tokenizer, runtime/container, context limit, generation settings and host configuration.
- [ ] Run one candidate at a time with the same CSM and Whisper services; record which unrelated services were stopped and restore them according to the deployment plan.
- [ ] Separate cold startup, warm-up and steady-state measurements.
- [ ] Repeat paired trials with interleaved ordering, including concurrency 1, 2, 4 and 8 where headroom permits.
- [ ] Measure process and cgroup peaks, host available memory, swap and allocator reservations. Do not double count GB10 unified memory.
- [ ] Collect wall energy or explicitly label GPU-only energy as an incomplete proxy.
- [ ] Capture first-token and end-to-end p50/p95/p99 latency, throughput, OOMs, retries, queue lengths and websocket recovery.
- [ ] Report confidence intervals, paired differences and safety-critical slices.
- [ ] Calculate cost per attempted, completed and accepted check-in. Include failed-request expense.
- [ ] Report no winner when a candidate fails the quality or safety gate.

## Work package 4: verify hosted alternatives and healthcare terms

Use primary provider price pages and contract documents. A similar model family name does not establish checkpoint equivalence.

- [ ] Include Groq, Together and Fireworks as research candidates, then confirm current catalog and regional availability.
- [ ] Treat hosted GPT-OSS as a substitute requiring evaluation.
- [ ] Treat Fireworks Nemotron 3.5 Lightning as a distinct checkpoint from local Nemotron Nano.
- [ ] Verify whether Together's listing named Ternary Bonsai 27B matches any desired artifact. Check duration, rate limits and terms of the zero-price listing.
- [ ] Get model, STT and TTS endpoint eligibility under an effective BAA; record exclusions and support access.
- [ ] Obtain minimum commitments, dedicated replica requirements, regions, availability targets, retention controls and negotiated prices.
- [ ] Capture voice consent and enrollment requirements; do not treat generic TTS as equivalent to the consented CSM experience.
- [ ] Review the entire data flow, including MLflow, logs, backups and EHR middleware. Record shared responsibilities.
- [ ] Price optional US-region restrictions separately. Do not claim HIPAA universally requires US-only hosting.
- [ ] Do not use Groq Compound or excluded free/preview services for PHI. Verify current official terms before any future PHI test.

HHS's [cloud guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html) supplies the regulatory baseline. Provider security announcements are supporting evidence, not executed agreements. Collect quotes without enrolling in paid services as part of this ticket unless separately authorized.

## Work package 5: produce the full bill and sensitivity analysis

- [x] Deliver the initial standard-library [projection calculator](../../scripts/project-costs.py) with Decimal arithmetic, source dates, explicit assumptions and patient-count override. Checked 100, 1,000 and 10,000 patients against the published tables. Measured benchmark and invoice work remain pending.

- [ ] Separate provider cash invoice, local incremental expense and fully allocated ownership cost.
- [ ] Include LLM input/output/cache/reasoning tokens, retries, STT, TTS and voice enrollment.
- [ ] Include equipment amortization, idle power, workload power, support, spare or redundant equipment and financing when applicable.
- [ ] Include database, object storage, trace storage, replicas, backup retention, restore testing, network and monitoring.
- [ ] Add EHR onboarding, interface engine, API access and per-transaction charges where applicable. Obtain vendor quotes.
- [ ] Add telephone/SMS service only for a future real telephony scenario; preserve zero carrier usage for the current browser POC.
- [ ] Add deployment engineering, security/privacy operations, legal/vendor review, annotation, clinical review and incident response assumptions.
- [ ] Include training and synthetic-generation run costs, discarded examples, review labor and occupied GB10 capacity.
- [ ] Vary patient volume, context length, output length, cache rate, retry rate, concurrency, clinician review time and hardware count.
- [ ] Model hosting the text model while retaining local voice, and a separate fully hosted application scenario.
- [ ] Publish break-even equations with capacity constraints. Do not infer scale from tokens alone.
- [ ] Reconcile a future authorized paid benchmark with an invoice and explain deviations.

## Work package 6: test additional clinical operations

- [ ] After a candidate passes the patient workflow gate, measure remaining memory and compute headroom.
- [ ] Add post-call summarization, logged-activity extraction and EHR sandbox export one at a time.
- [ ] Repeat patient latency and quality measurements under each combined workload.
- [ ] Record workload scheduling and peak overlap, rather than claiming that freed weight bytes guarantee another application fits.
- [ ] Keep clinician approval for plan changes and clinical actions. No autonomous production EHR write is in scope.

## Acceptance criteria

The report includes reproducible source data, MLflow run links, paired quality results and confidence intervals. Its local memory and power values are measured, with collection methods documented. Hosted model identity and rates are dated, and contract-dependent costs remain explicitly unresolved until quoted. The final monthly bill contains all known categories and names every excluded cost. A reviewer can recalculate each total from the supplied workload and price artifacts.

The decision states whether Bonsai matches the required behavior, whether it releases useful device capacity and whether it changes cost per accepted workflow. A failed equivalence result is a valid experiment outcome. No claim of lossless quantization, free ownership or clinical deployment readiness may substitute for the evidence.

## Deliverables

1. Versioned workload and price artifacts, a calculation script and a small arithmetic verification fixture.
2. MLflow instrumentation, experiment links, trace examples without sensitive content and paired benchmark runs.
3. A provider eligibility and quote worksheet with endpoint-specific BAA status and unresolved questions.
4. Updated cost and capacity report with pilot, planning and larger-volume bills.
5. A decision record connecting any model promotion and added GB10 workload to the measured results.
