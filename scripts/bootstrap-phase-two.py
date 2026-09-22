#!/usr/bin/env python3
"""Create empty MLflow evaluation datasets without inventing labels or scores."""
import json
import os

import mlflow
from mlflow.genai.datasets import create_dataset, search_datasets


def main():
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5210"))
    experiment = mlflow.set_experiment("Anchor Phase Two Evaluation")
    client = mlflow.MlflowClient()
    client.set_experiment_tag(experiment.experiment_id, "project", "anchor-nvidia-gb10")
    client.set_experiment_tag(experiment.experiment_id, "phase", "2")
    client.set_experiment_tag(experiment.experiment_id, "status", "awaiting-reviewed-data-and-baseline")
    datasets = []
    for split in ("candidates", "development", "holdout", "production-replay"):
        name = f"anchor-phase-two-{split}"
        matches = search_datasets(experiment_ids=[experiment.experiment_id], filter_string=f"name = '{name}'")
        if len(matches) > 1:
            raise RuntimeError(f"Multiple datasets named {name}; resolve explicitly before proceeding")
        dataset = matches[0] if matches else create_dataset(
            name=name,
            experiment_id=experiment.experiment_id,
            tags={"project": "anchor-nvidia-gb10", "split": split,
                  "data_policy": "synthetic-or-approved-deidentified-only",
                  "review_status": "empty-awaiting-human-review"},
        )
        datasets.append({"name": name, "dataset_id": dataset.dataset_id})
    print(json.dumps({"experiment_id": experiment.experiment_id,
                      "experiment_name": experiment.name, "datasets": datasets}, indent=2))


if __name__ == "__main__":
    main()
