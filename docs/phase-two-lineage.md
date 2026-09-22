# Anchor phase two lineage

Recorded September 22, 2026. Phase two will compare Bonsai with the existing Nemotron application on the GB10. The aim is to reduce total workload memory while preserving measured behavior, then test whether the remaining capacity can support additional clinical operations. Comparable quality, lower operating cost, and useful spare capacity are hypotheses until the paired application evaluation establishes them.

## Application history

| Stage | Source | What the source establishes |
| --- | --- | --- |
| CareLine blueprint | [`hybrid-ai-blueprints`, `5f967406`](https://github.com/ChaiWithJai/hybrid-ai-blueprints/tree/5f967406), branch `blueprint/careline-wellness-checkin` | Anchor's README identifies this as its original blueprint. The GB10 additions came from the T7 snapshot dated August 22, 2026. The snapshot date is provenance, not proof of public availability. |
| Anchor NVIDIA proof of concept | [Anchor source at `7cff36040cda52e67c97dc03e5656f62c917f570`](https://github.com/ChaiWithJai/anchor-nvidia-gb10/tree/7cff36040cda52e67c97dc03e5656f62c917f570) | The repository narrows the blueprint to a local NVIDIA runtime with consent, durable clinical state, deterministic safety handling, and an optional bounded agent handoff. |
| Ambient messaging extension | [WebSocket messaging](websocket-messaging.md) | Text messages enter the existing application workflow. Transport does not grant the agent new clinical authority. Deployment and smoke-test evidence belong to the corresponding MLflow run. |
| Bonsai phase two | This document and the phase-two evaluation plan | A proposed model comparison and improvement program. A running standalone Bonsai endpoint does not establish an Anchor deployment or successful clinical evaluation. |

The initial application revision above is the baseline inspected for this document. Later source changes must receive their own revision in evaluation manifests.

## Preserve the application contract

The [architecture](../SYSTEM-ARCHITECTURE.md), [data model](../DATA-MODEL.md), and [Compose configuration at the baseline revision](https://github.com/ChaiWithJai/anchor-nvidia-gb10/blob/7cff36040cda52e67c97dc03e5656f62c917f570/compose.nvidia.yml) define the existing contract.

FastAPI owns prompt assembly, consent checks, workflow, and deterministic risk scoring. MongoDB 8 owns patients, plan revisions, signals, calls, transcripts, memories, alerts, and audit records. Nemotron produces bounded conversational text through an OpenAI-compatible interface. Sesame CSM-1B provides local speech, while Whisper tiny.en transcribes microphone input. Raw microphone audio is processed in memory.

The model has no authority to change a care plan. Concerning turns commit their alert before the optional OpenClaw handoff inside OpenShell. A failed handoff remains visible in MongoDB, and the patient response must not claim a clinician was contacted. The optional tunnel is a synthetic-data demonstration transport.

Phase two should change the configured language-model endpoint and its runtime first. Keep the prompt, retrieved records, speech models, safety rules, and MongoDB behavior fixed for the first comparison. Record subsequent changes as separate interventions so memory savings and quality changes have an attributable cause. The existing application already accepts OpenAI-compatible model traffic, which supports a narrow integration experiment without a new orchestration service.

## Exact model identities

| Role | Identity | Evidence and limits |
| --- | --- | --- |
| Anchor baseline | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` | The baseline Compose file selects this model for both normal and strong model settings. Its default NVIDIA vLLM image is `nvcr.io/nvidia/vllm:26.05.post1-py3`, its maximum context is 8192, and its GPU memory utilization setting is 0.35. Capture the actual image digest, downloaded model revision, weight hashes, and effective arguments before comparison. A configured memory fraction is not measured memory use. |
| First Bonsai candidate | `prism-ml/Ternary-Bonsai-2-27B-gguf` | The intended name is **Ternary Bonsai 2 27B**, not a 227B model. The [pinned model card](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/6ed5e12bf84b7a63069882c91dd9e9218647d17b/README.md) names `Qwen/Qwen3.8-27B` as its base model. |
| Recorded GB10 artifact | `Ternary-Bonsai-2-27B-PQ2_0.gguf` | A September 18 local identity snapshot binds the observed server path to a previously verified checkpoint at revision `6ed5e12bf84b7a63069882c91dd9e9218647d17b`. Recorded SHA-256 is `3907dc1658db1f78a9826bf8d5bcb8dc65db0d466388937af57f2294fae62ec1`, file size is 7,206,168,928 bytes, and server build reports `b1-d8f26ee`. The snapshot did not recalculate the file hash per request. Reverify the active deployment before evaluation. |
| Earlier Bonsai generation | `prism-ml/Ternary-Bonsai-27B-gguf` | The earlier family is a separate candidate. Historical cards and tests must retain their original identity and must not be relabeled as Bonsai 2. |

The pinned Bonsai 2 card reports an average of 84.78 across 14 thinking-mode benchmarks and 98.2% of its FP16 reference average. Those are publisher measurements, not Anchor results or evidence of zero quality loss. The card's compact footprint headline also does not describe every available GGUF file. Use the exact file and measured process memory in deployment comparisons.

A release configuration is the checkpoint, weight format, runtime revision, backend, hardware, and application contract together. A repository name alone is insufficient. Record context allocation, parallel slots, cache format, reasoning settings, output limit, projector loading, and any speculative decoder alongside that configuration.

## Compression and training claims

Lossless representation of an existing ternary checkpoint is different from preserving every capability of its original full-precision model. More compact storage of a ternary checkpoint does not establish lossless conversion from arbitrary full-precision weights, equal clinical performance, or parity with a hosted frontier model.

Quantization, pruning, and fine-tuning are separate experiments. There is no requirement to prune before fine-tuning. Start with the published candidate and determine which application failures remain. A later training experiment must identify its trainable representation, supported training implementation, objective, and export route back to the deployed runtime. An inference GGUF file alone does not establish a supported training pipeline.

Human labels can support supervised fine-tuning, preference optimization, or reinforcement learning. Evaluating an output and storing reviewer feedback does not itself update model weights. Preserve the distinction in MLflow so a prompt improvement, a new dataset, and a trained checkpoint remain different changes.

Synthetic examples generated locally avoid a hosted inference charge, but generation still consumes compute, electricity, storage, review time, and engineering effort. Teacher-generated answers require review and held-out evaluation. Keep generator identity, source rights, prompt version, seed, parent example, and acceptance decision with every accepted record.

## EHR and clinical operations boundary

EHR integration is proposed work. The current proof of concept does not establish a deployed EHR connector or production clinical suitability. A first integration can map approved synthetic encounter events into the existing persisted entities, then expose draft summaries or follow-up work for human review. Model output must not silently become an authoritative chart entry or care-plan revision.

Keep source event identifiers, event time, ingestion time, consent scope, transformation version, reviewer identity, and correction history in the integration design. Use separate test identities and fixtures for synthetic records. Reusing production events, recordings, or notes in training requires a separately approved data boundary, retention policy, and access model.

Candidate spare-capacity workloads include draft encounter summaries, reconciliation of logged activities, and review queues. Evaluate one additional workload at a time with the ambient agent active. Measure end-to-end latency, memory pressure, failure rate, and the effect on the patient call. A smaller weight file alone does not establish safe concurrency or useful capacity.

## Evidence ledger

The local evidence lab is private working material. It is not copied wholesale into this public documentation. Source files were inspected without restarting services or changing historical evaluation datasets.

| Source | Visibility and observation | SHA-256 of inspected local source |
| --- | --- | --- |
| Anchor `SYSTEM-ARCHITECTURE.md` at the baseline revision | Public repository, inspected September 22 | `ac4c923928155408ca6e533614dc4a1b7541615d850fd2077c6a5ec32e19b201` |
| Anchor `compose.nvidia.yml` working source | Public repository source, inspected September 22 | `7d6516c0e3fbcd0d056084e31a73a7582857e924dcc2d9f076dad7a312971568` |
| Private deployment identity snapshot | Private identity observation dated September 18, inspected September 22 | `7dc923679cdff7f2988c6b8357d7bc333e0e675f09e57c3f7178b3ee6d042b15` |
| Private historical source archive | Private historical source archive, inspected September 22 | `8e3631884232dc2fad59edebb39976239220058898ae2ca0ef4bdd751df4c3f2` |
| Private historical source relationships | Private historical source relationships, inspected September 22 | `bf5e2b2a53072b49efe2e4e72df81a2e6de72d9e7c0da1f783799a917d24eb38` |

The Bonsai lab report was collected September 14 to 15 and is a historical snapshot. Its private-preview terminology and model inventory must not override the later pinned Bonsai 2 card. New phase-two runs should attach this document and a source manifest with retrieval times, URLs, revisions, hashes, and visibility. Preserve the original source observations when newer evidence supersedes them.
