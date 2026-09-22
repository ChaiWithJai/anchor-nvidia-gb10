#!/usr/bin/env python3
"""Record a deployment or verification command in the existing MLflow server.

Run on the GB10 with its MLflow Python environment. This adds no app service.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import time

import mlflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--parent-run")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5210"))
    mlflow.set_experiment("Anchor NVIDIA GB10")
    tags = {"project": "anchor-nvidia-gb10"}
    if args.parent_run:
        tags["mlflow.parentRunId"] = args.parent_run
    with mlflow.start_run(run_name=args.name, tags=tags) as run:
        print("MLflow run:", run.info.run_id, flush=True)
        mlflow.log_param("command", command)
        started = time.monotonic()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "command.log"
            with mlflow.start_span(name=args.name, span_type="TOOL") as span:
                span.set_inputs({"command": command})
                with path.open("w") as output:
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for line in process.stdout:
                        print(line, end="", flush=True)
                        output.write(line)
                    code = process.wait()
                span.set_outputs({"exit_code": code})
                if code:
                    span.set_status("ERROR")
            mlflow.log_metric("duration_seconds", time.monotonic() - started)
            mlflow.log_metric("exit_code", code)
            mlflow.log_artifact(str(path), "verification")
            if code:
                mlflow.end_run(status="FAILED")
            return code


if __name__ == "__main__":
    raise SystemExit(main())
