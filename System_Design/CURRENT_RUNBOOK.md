# Current Runbook

## Scope

This document describes how to run the current A22 stack end to end:

- local frontend
- local edge-backend
- remote `qwen-server` via vLLM
- remote `orchestrator`
- SSH tunnel from local to remote

## Current architecture

The current runtime chain is:

1. browser frontend records text or audio
2. local `edge-backend` normalizes the turn
3. local BELLE ASR converts audio to text when `input_type=audio`
4. local `edge-backend` forwards a structured `/chat` request to remote `orchestrator`
5. remote `orchestrator` calls the remote LLM service
6. remote response returns to local backend and then to the frontend

## Start order

Use this order:

1. Start remote `qwen-server`
2. Start remote `orchestrator`
3. Create the SSH tunnel
4. Start local Docker services
5. Verify local BELLE warmup
6. Run end-to-end tests

## Remote server: qwen-server

Recommended server path:

```bash
/home/zifeng/siyuan/A22/A22_wmzjbyGroup/remote/qwen-server
```

Recommended model path:

```bash
/data/zifeng/siyuan/A22/models/Qwen2.5-7B-Instruct
```

Create and prepare the environment:

```bash
cd /home/zifeng/siyuan/A22/A22_wmzjbyGroup/remote
mkdir -p qwen-server
cd qwen-server
uv venv --python /usr/bin/python3.11 .venv
source .venv/bin/activate
uv pip install --upgrade pip
uv pip install vllm
```

Start vLLM on a selected GPU:

```bash
cd /home/zifeng/siyuan/A22/A22_wmzjbyGroup/remote/qwen-server
source .venv/bin/activate
export CUDA_VISIBLE_DEVICES=<cuda_id>
python -m vllm.entrypoints.openai.api_server \
  --host 127.0.0.1 \
  --port 8000 \
  --model /data/zifeng/siyuan/A22/models/Qwen2.5-7B-Instruct \
  --served-model-name Qwen2.5-7B-Instruct \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --trust-remote-code
```

Notes:

- `<cuda_id>` can be `0`, `1`, or `2`
- this selects a single physical GPU for the vLLM process
- the current 7B model can run as a single-GPU deployment

Verify on the server:

```bash
curl http://127.0.0.1:8000/v1/models
```

## Remote server: orchestrator

Prepare the environment:

```bash
cd /home/zifeng/siyuan/A22/A22_wmzjbyGroup/remote/orchestrator
uv venv --python /usr/bin/python3.11 .venv
source .venv/bin/activate
uv sync
```

If `.venv` already exists:

```bash
cd /home/zifeng/siyuan/A22/A22_wmzjbyGroup/remote/orchestrator
source .venv/bin/activate
uv sync
```

Start orchestrator:

```bash
cd /home/zifeng/siyuan/A22/A22_wmzjbyGroup/remote/orchestrator
source .venv/bin/activate
export LLM_PROVIDER=qwen
export LLM_MODEL=Qwen2.5-7B-Instruct
export LLM_API_BASE=http://127.0.0.1:8000/v1
export LLM_API_KEY=EMPTY
export LLM_REQUEST_TIMEOUT_SECONDS=60
uv run uvicorn app:app --host 127.0.0.1 --port 19000
```

Verify on the server:

```bash
curl http://127.0.0.1:19000/health
```

## Local machine: SSH tunnel

Create the tunnel from local to remote:

```bash
ssh -N -L 19000:127.0.0.1:19000 <server_user>@<server_host>
```

Verify locally:

```bash
curl http://127.0.0.1:19000/health
curl -X POST http://127.0.0.1:19000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-001","turn_id":1,"user_text":"hello","input_type":"text"}'
```

## Local machine: frontend and edge-backend

Start local services:

```bash
cd /home/siyuen/docker_ws/A22
docker compose -f compose.yaml -f compose.local.yaml up -d --force-recreate
```

Check service status:

```bash
docker compose -f compose.yaml -f compose.local.yaml ps
docker compose -f compose.yaml -f compose.local.yaml logs -f edge-backend
```

## Local BELLE warmup

The local `edge-backend` preloads the BELLE ASR model during FastAPI startup.

The backend is considered ready only after the log shows:

- `asr_warmup_start`
- `asr_warmup_ready`

Watch the local logs:

```bash
tail -f /home/siyuen/docker_ws/A22/logs/edge-backend/edge-backend-events-*.log
```

Or use the compact listener:

```bash
python3 /home/siyuen/docker_ws/A22/a22_demo/listen_bridge.py
```

## End-to-end test

Test remote orchestrator from local:

```bash
curl http://127.0.0.1:19000/health
```

Test the local edge-backend directly:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-001","turn_id":1,"user_text":"测试文本链路","input_type":"text"}'
```

Test the browser UI:

```text
http://localhost
```

Recommended test order:

1. send one text turn
2. verify remote response is returned
3. send one audio turn
4. check `asr_transcription` in local logs
5. check `bridge_outbound` and `bridge_inbound`

## Shutdown

Stop local containers:

```bash
cd /home/siyuen/docker_ws/A22
docker compose -f compose.yaml -f compose.local.yaml down
```

Stop the SSH tunnel:

```bash
pkill -f "ssh -N -L 19000:127.0.0.1:19000"
```

Stop remote services by interrupting their running terminals.
