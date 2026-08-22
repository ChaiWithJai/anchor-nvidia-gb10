#!/usr/bin/env bash
set -euo pipefail

tests_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mongodb_dir="$(cd "${tests_dir}/.." && pwd)"
project_data_dir="$(cd "${mongodb_dir}/.." && pwd)"

python3 "${project_data_dir}/generate_mongodb.py"
python3 "${tests_dir}/test_generated_data.py"
node --check "${mongodb_dir}/schema.mongodb.js"
node --check "${mongodb_dir}/seed.mongodb.js"
node --check "${tests_dir}/test_database.mongodb.js"

if [[ "${RUN_MONGODB_INTEGRATION:-0}" == "1" ]]; then
  if ! command -v mongosh >/dev/null 2>&1; then
    echo "mongosh is required when RUN_MONGODB_INTEGRATION=1" >&2
    exit 1
  fi
  mongodb_uri="${MONGODB_URI:-mongodb://localhost:27017}"
  mongosh "${mongodb_uri}" --quiet --file "${mongodb_dir}/schema.mongodb.js"
  mongosh "${mongodb_uri}" --quiet --file "${mongodb_dir}/seed.mongodb.js"
  mongosh "${mongodb_uri}" --quiet --file "${tests_dir}/test_database.mongodb.js"
else
  echo "MongoDB integration tests skipped. Set RUN_MONGODB_INTEGRATION=1 to enable them."
fi
