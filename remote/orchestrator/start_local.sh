#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -d ".venv" ]]; then
  echo "Missing .venv in remote/orchestrator. Please run: uv venv .venv --python 3.11 && uv sync"
  exit 1
fi

source .venv/bin/activate

export SPEECH_SERVICE_ENABLED="${SPEECH_SERVICE_ENABLED:-true}"
export SPEECH_SERVICE_BASE="${SPEECH_SERVICE_BASE:-http://127.0.0.1:19100}"
export SPEECH_SERVICE_TIMEOUT_SECONDS="${SPEECH_SERVICE_TIMEOUT_SECONDS:-300}"

exec python -m uvicorn app:app --host 0.0.0.0 --port "${ORCHESTRATOR_PORT:-19000}"
