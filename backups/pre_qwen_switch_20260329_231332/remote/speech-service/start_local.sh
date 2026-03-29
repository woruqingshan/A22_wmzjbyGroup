#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -d ".venv" ]]; then
  echo "Missing .venv in remote/speech-service. Please run: uv venv .venv --python 3.11 && uv sync"
  exit 1
fi

source .venv/bin/activate

export UV_LINK_MODE="${UV_LINK_MODE:-copy}"
export TMP_DIR="${TMP_DIR:-/tmp/a22/speech}"
mkdir -p "${TMP_DIR}"

if [[ -d "${VIRTUAL_ENV}/lib/python3.11/site-packages/nvidia" ]]; then
  NVIDIA_LIB_PATHS="$(echo "${VIRTUAL_ENV}"/lib/python3.11/site-packages/nvidia/*/lib | tr ' ' ':')"
  export LD_LIBRARY_PATH="${NVIDIA_LIB_PATHS}:${LD_LIBRARY_PATH:-}"
fi

export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

DEFAULT_MODEL_CACHE="$(ls -d "${HOME}"/.cache/huggingface/hub/models--BELLE-2--Belle-whisper-large-v3-turbo-zh/snapshots/* 2>/dev/null | head -n 1 || true)"
if [[ -n "${DEFAULT_MODEL_CACHE}" ]]; then
  export ASR_MODEL="${ASR_MODEL:-${DEFAULT_MODEL_CACHE}}"
else
  export ASR_MODEL="${ASR_MODEL:-BELLE-2/Belle-whisper-large-v3-turbo-zh}"
fi

export ASR_PROVIDER="${ASR_PROVIDER:-belle_whisper}"
export ASR_LANGUAGE="${ASR_LANGUAGE:-zh}"
export ASR_DEVICE="${ASR_DEVICE:-cuda:0}"
export ASR_WARMUP_ENABLED="${ASR_WARMUP_ENABLED:-false}"

exec python -m uvicorn app:app --host 0.0.0.0 --port "${SPEECH_PORT:-19100}"
