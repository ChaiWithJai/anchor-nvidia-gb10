# Phase two cost and capacity analysis

Status: research and experiment specification, 2026-09-22. Prices are public list prices read on that date. Dollar amounts are USD, before tax. No provider was purchased or benchmarked for this report. No clinical data was sent to a provider.

Phase two tests whether Bonsai can preserve Anchor's required behavior while reducing memory and cost. The local comparison is `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` against `prism-ml/Ternary-Bonsai-2-27B-gguf`, variant `Ternary-Bonsai-2-27B-PQ2_0`. Pin revisions, artifact digests, tokenizer, runtime and settings in the experiment. Other Bonsai family sizes enter as separate candidates after their deployment artifacts are verified.

Neither equivalent quality nor a memory reduction has been measured here. Quantization, pruning and fine-tuning each require evaluation. Smaller weights do not guarantee the same behavior, lower peak memory, or faster responses. Self-hosted generation avoids an external per-token invoice but still consumes equipment, electricity, staff time and capacity.

## Reproduce the initial projection

Tracking issue: [#22](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/22). The standard-library [projection calculator](../scripts/project-costs.py) emits JSON with Decimal-based monetary calculations, dated source URLs and explicit assumptions.

```bash
python3 scripts/project-costs.py --patients 1000
```

Use `--patients 100` or `--patients 10000` for the other volume scenarios. The fixed monthly budget stays constant for sensitivity analysis; the calculator does not establish that one GB10 can handle those volumes. Measurements, provider contracts and invoice reconciliation remain pending.

## Workload and accounting boundary

The current application uses browser calls, local Whisper tiny.en and local CSM-1B. It does not make public telephone calls or integrate with a production EHR. The cost scenarios retain browser calling. Telephone service and production EHR charges remain additional, quoted items.

The planning unit is one completed patient check-in. The following are assumptions, not observations. The input count includes repeated history, plan context and instructions across all turns. Generated output includes any billed reasoning tokens. Instrument actual counts separately for each tokenizer.

| Assumption | Small pilot | Planning case | Larger service |
| --- | ---: | ---: | ---: |
| Enrolled patients | 100 | 1,000 | 10,000 |
| Check-ins per patient per month | 8 | 8 | 8 |
| Check-ins per month | 800 | 8,000 | 80,000 |
| LLM calls per check-in | 6 | 6 | 6 |
| Input tokens per check-in, total | 12,000 | 12,000 | 12,000 |
| Output tokens per check-in, total | 1,500 | 1,500 | 1,500 |
| Monthly input tokens | 9.6 million | 96 million | 960 million |
| Monthly output tokens | 1.2 million | 12 million | 120 million |
| Audio minutes per check-in | 5 | 5 | 5 |
| Monthly audio hours | 66.67 | 666.67 | 6,666.67 |

Model retries and failed attempts are initially zero in the table, then varied below. Deterministic safety replies should retain their actual zero LLM usage rather than inherit an average token count. Post-call summaries, embeddings, judges, synthetic generation and training get separate workload rows so they are not hidden inside patient inference.

## Published inference prices and hypothetical invoices

The rows below are alternatives, not charges to add together. GPT-OSS and hosted Lightning are substitute models requiring their own quality evaluation. No listed provider has been established here as hosting the exact local Bonsai 2 or Nemotron Nano artifact.

| Provider and model | Input per million | Output per million | Pilot LLM invoice | Planning LLM invoice | Larger LLM invoice |
| --- | ---: | ---: | ---: | ---: | ---: |
| Groq, GPT-OSS 120B | $0.15 | $0.60 | $2.16 | $21.60 | $216.00 |
| Together, GPT-OSS 120B | $0.15 | $0.60 | $2.16 | $21.60 | $216.00 |
| Fireworks, GPT-OSS 120B, standard | $0.15 | $0.60 | $2.16 | $21.60 | $216.00 |
| Fireworks, Nemotron 3.5 Lightning 30B A3B, standard | $0.05 | $0.20 | $0.72 | $7.20 | $72.00 |
| Together, listing named Ternary Bonsai 27B | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 |

Sources: [Groq models and prices](https://console.groq.com/docs/models), [Together prices](https://www.together.ai/pricing), and [Fireworks serverless prices](https://docs.fireworks.ai/serverless/pricing). Together's zero-price listing does not identify the local Bonsai 2 artifact. Its identity, limits, duration, availability and eligibility for protected health information remain unverified. Do not budget a production contract from that listing alone. Recheck all rates before procurement.

For example, the planning GPT-OSS invoice is `96 × $0.15 + 12 × $0.60 = $21.60`. There is no assumed cache discount, batch discount or enterprise minimum. Public prices do not establish an applicable healthcare contract price.

Groq lists Whisper large-v3-turbo at $0.04 per audio hour. At the assumed volumes, token-independent transcription would add approximately $2.67, $26.67 or $266.67. Request minimums, retries and audio duration rounding require verification before billing estimates. Whisper large-v3-turbo is a substitute for local tiny.en, and it needs a separate transcription evaluation. The planning LLM plus transcription subtotal is therefore $48.27 before TTS and the rest of the application. [Groq model pricing](https://console.groq.com/docs/models).

An alternative dedicated-capacity illustration uses one Fireworks H100 at $8 per hour for 730 hours, or $5,840 per month. A region-restricted deployment at the published 1.5 multiplier would be $8,760. Hardware suitability, model support and actual replica count are unverified. Dedicated deployment does not mean that a particular GGUF runtime or model is supported. [Fireworks dedicated pricing](https://fireworks.ai/pricing).

## Illustrative full monthly operating budget

A fully allocated cost includes shared operations and amortized setup work. The budget below is a planning example for 8,000 check-ins per month. Every amount in this table is an assumption, except the hosted token price above. The amounts are neither quotes nor a claim that one GB10 can serve this load.

| Monthly item | Local GB10 | Hosted text, local voice |
| --- | ---: | ---: |
| Equipment, assumed $5,000 over 36 months | $138.89 | $138.89 |
| Wall electricity, assumed 0.20 kW × 730 h × $0.20/kWh | $29.20 | $29.20 |
| Hardware support and replacement reserve | $50.00 | $50.00 |
| Text inference invoice | $0.00 | $21.60 |
| Local STT and TTS incremental vendor invoice | $0.00 | $0.00 |
| Encrypted storage and backup allowance | $50.00 | $50.00 |
| Application, database, MLflow and monitoring operations, 8 h × $100 | $800.00 | $800.00 |
| Security and privacy operations, 4 h × $125 | $500.00 | $500.00 |
| Initial deployment and EHR engineering, $12,000 over 24 months | $500.00 | $500.00 |
| Model evaluation and annotation, 4 h × $100 | $400.00 | $400.00 |
| Total allocated planning budget | $2,468.09 | $2,489.69 |
| Allocated cost per check-in | $0.309 | $0.311 |

The hosted comparison retains the GB10 for voice and the application, so its equipment cost is intentionally unchanged. Replacing the whole stack with hosted voice and application services requires a new estimate. A smaller device for local voice is another scenario, after capacity testing. Local Nemotron and Bonsai have the same assumed fixed budget until measurements show different power, capacity or staffing requirements.

The current POC has no raw microphone recording archive. If policy later permits storage, 16 kHz mono 16-bit PCM is 1.92 MB per minute. Forty thousand minutes would add 76.8 GB per month before replicas, backups or generated voice storage. Retention duration, database records, trace volume, backup copies, audit events and retrieval traffic must be priced explicitly. The $50 allowance is not a storage vendor quote.

The budget excludes direct patient care staff, telephone carrier and phone-number charges, EHR vendor access fees, taxes, financing, legal review, insurance, high availability and disaster recovery hardware. Each excluded item has an explicit procurement line in the issue. A final clinical service budget remains `illustrative subtotal + quoted missing items + required capacity`. A universal HIPAA surcharge does not exist in the evidence collected here.

A hosted TTS quote must specify characters or audio minutes, voice enrollment, consent, generated-audio retention and applicable BAA coverage. CSM voice cloning cannot be priced as an interchangeable generic voice without validating the product requirement. Keep STT, TTS and LLM charges separate when calculating the anticipated bill.

## Sensitivity and opportunity sizing

| Change from planning case | GPT-OSS text invoice | Interpretation |
| --- | ---: | --- |
| Base, 96M input and 12M output | $21.60 | No cache discount or retries |
| Input context doubles | $36.00 | Repeated history drives input expense |
| Output and reasoning tokens double | $28.80 | Bill all generated tokens |
| All calls require 10% extra attempts | $23.76 | Assumes proportional token usage |
| Patient volume grows tenfold | $216.00 | Capacity and staff may grow nonlinearly |

At $0.0027 per check-in, a token-only GPT-OSS bill reaches the assumed $218.09 monthly local equipment, electricity and reserve subtotal at about 80,774 check-ins. The arithmetic does not establish a feasible GB10 throughput or a full-cost break-even point. Local voice and application hardware may remain necessary under either option. At the published free Bonsai listing, no token-price break-even exists while that price applies.

The proposed opportunity is measurable clinical workflow quality, privacy control, reliable latency and useful remaining device capacity. Token savings alone may be small at these published rates. Value from staff time saved must come from observed minutes and loaded labor rates, with adverse events and review time included.

## Official MLflow cost workflow

Use the existing tracking service and separate experiments or runs for deployment, matched quality evaluation and economics. Record its exact installed version and storage configuration before changing it. MLflow's [official token and cost tracking guide](https://mlflow.org/docs/latest/genai/tracing/token-usage-cost/) requires version 3.10 or newer for cost tracking and the server's `genai` extra. It exposes span and trace token counts, estimated USD cost, and experiment-level cost charts.

Implement the following project-specific extensions around that documented workflow.

1. Trace each app request and its LLM, STT, TTS, database, EHR and agent operations. Attach pseudonymous session IDs, dataset row IDs, model revision and prompt version. Keep private payloads outside public artifacts.
2. Capture actual usage. For custom local endpoints, populate `mlflow.chat.tokenUsage` with `input_tokens`, `output_tokens` and `total_tokens`. Missing usage stays unknown. Count cancelled requests and failed attempts where usage is available.
3. Populate `mlflow.llm.cost` with `input_cost`, `output_cost` and `total_cost` only for the applicable token invoice. Record a known zero external inference charge explicitly for local inference. An unrecognized model or missing price must not silently become a free service.
4. Store the assumed price schedule, source URL, effective date, currency, cache rules, contract status and model identity as a versioned artifact. Keep projected hosted costs separate from actual local invoices.
5. Log full-cost metrics separately, including `energy_kwh`, `wall_power_watts_mean`, `hardware_usd_allocated`, `staff_usd_allocated`, `stt_usd`, `tts_usd`, `storage_usd`, `ehr_usd`, `evaluation_usd`, `training_usd` and `tco_usd`. Do not place amortization into token cost fields.
6. Join cost with blinded human ratings and deterministic safety results on the same frozen rows. Report cost per attempted check-in, completed check-in and accepted check-in. An accepted check-in satisfies the predefined quality and safety criteria.
7. Export the calculation inputs and derived table as artifacts. Reconcile hosted estimates with a real invoice when an authorized paid test happens. No paid provider test is part of this documentation change.

Local energy comes from a wall meter where available. GPU telemetry excludes some CPU, memory, cooling and power supply overhead. Record telemetry source and uncertainty, then separate idle from incremental request energy without double counting the monthly idle budget.

## Capacity experiment and remaining work on the GB10

Measure the entire application with one candidate at a time on the same machine. Preserve the same voice models, context, concurrency, prompt, request sequence and application commit. Run warm-up separately, then repeated paired trials with interleaved candidate order. Record cold startup independently.

| Measurement | Required evidence |
| --- | --- |
| Memory | Weight bytes, process RSS, cgroup peak, system available memory and swap, sampled throughout the workload |
| Unified-memory accounting | Avoid adding overlapping CPU and GPU allocations; record method and allocator reservation separately |
| Throughput | Input and output tokens per second plus completed check-ins per minute |
| Latency | Time to first token, per-turn end-to-end, STT, TTS and websocket round-trip p50/p95/p99 |
| Reliability | OOMs, queue depth, timeouts, disconnect recovery, rejected requests and retry cost |
| Quality | Safety/escalation failures, plan grounding, structured-output validity, memory correctness and clinician acceptance |
| Capacity | Peak concurrent check-ins that satisfy predefined quality and latency limits with a reserve |

Test concurrency 1, 2, 4 and 8 only while the host has safe operating headroom. Pick numeric latency limits and an equivalence margin before reading model results. Report uncertainty and per-slice failures; average scores can hide a clinical regression.

After a candidate passes, measure concurrent post-call summarization, clinical activity extraction and an EHR sandbox export. Add one workload at a time. Any claimed freed memory must support an observed additional workload without harming patient response latency. No autonomous diagnosis, medication changes or production EHR writes are introduced by the experiment.

## Healthcare procurement boundary

HHS describes a cloud provider maintaining or processing electronic protected health information as a business associate in the relevant circumstances, including some encrypted-storage cases. A suitable BAA and risk analysis are required; a provider's marketing claim alone does not establish the customer's compliance. HHS does not impose a blanket US-only hosting rule, although geography can affect risk and contractual requirements. [HHS cloud guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html).

| Provider | Public evidence | Remaining contract and service questions |
| --- | --- | --- |
| Groq | [Published customer BAA](https://console.groq.com/docs/legal/customer-business-associate-addendum) defines covered services and excludes beta, preview, trial and free services. | Obtain an effective agreement; confirm the selected paid model endpoint, audio services, retention, logging and limits. [Compound is explicitly excluded](https://console.groq.com/docs/compound) from PHI use at present. |
| Together | [Security announcement](https://www.together.ai/blog/soc-2-compliance) describes HIPAA practices and BAAs. | Obtain actual BAA scope, minimum spend, region, support terms and endpoint eligibility. Free Bonsai listing eligibility is unknown. |
| Fireworks | [Security announcement](https://fireworks.ai/blog/fireworks-ai-achieves-soc-2-type-ii-and-hipaa-compliance) states HIPAA support. | Confirm current contract, BAA, selected model and service tier, region restrictions and retention. An older announcement is not an executed agreement. |
| Local GB10 | Data can remain in the intended local boundary. | Budget access controls, encryption, backup recovery, patching, audit retention and operator responsibilities; review every external service that receives data. |

Include MLflow, backups, error reporting, remote access, voice, EHR middleware and support access in the data-flow inventory. Trace exports can contain health information even when the model is local. Use synthetic data for initial measurements. Quote optional regional restrictions separately from actual legal obligations.

## Deliverables and decision

The separate [cost-analysis ticket](issues/phase-two-cost-analysis.md) requests the instrumentation, paired trials, procurement worksheet and reproducible report. The final decision must contain measured local results, current quoted hosted terms and a quality-qualified cost table. Until those exist, the numbers above remain a transparent planning scenario rather than a savings claim.
