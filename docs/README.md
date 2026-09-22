# Anchor documentation

Phase one proves the local NVIDIA application. Phase two uses that
application as a fixed baseline for evaluation-driven development with Bonsai.

The implementation plan is [issue #21](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/21).
The cost and capacity work is [issue #22](https://github.com/ChaiWithJai/anchor-nvidia-gb10/issues/22).

| Document | Purpose |
| --- | --- |
| [System architecture](../SYSTEM-ARCHITECTURE.md) | Defines the current services, trust boundaries, and workload. |
| [Data model](../DATA-MODEL.md) | Defines persisted records and their relationships. |
| [GB10 runbook](../GB10-RUNBOOK.md) | Explains startup and workload verification. |
| [WebSocket messaging](websocket-messaging.md) | Explains text messaging through the existing application and MLflow command tracking. |
| [Phase-two lineage](phase-two-lineage.md) | Records application and model ancestry, exact identities, and evidence limits. |
| [Phase-two evaluation](phase-two-evaluation.md) | Plans annotation, paired evaluation, improvements, and deployment monitoring. |
| [Phase-two cost analysis](phase-two-cost-analysis.md) | Defines local measurements, hosted scenarios, and cost assumptions. |

The documentation stays versioned with the implementation so each MLflow run
can identify its source revision. Preserve separate identities for source
events, annotations, datasets, model checkpoints, application versions, and
deployment manifests. A result applies to the recorded combination of those
artifacts.
