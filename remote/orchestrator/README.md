# orchestrator (remote skeleton)

Minimal HTTP service implementing **contract v0** (`shared/contracts/api_v1.md`).

## Run without Docker (lab server)

```bash
cd remote/orchestrator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 9000
```

Bind to `127.0.0.1` when exposing only via SSH tunnel from your laptop.

## Run with Docker (on a host that has Docker)

From repository root:

```bash
docker compose -f compose.yaml -f compose.remote.yaml up -d orchestrator
```

## Endpoints

- `GET /health`
- `POST /chat`

See `../../shared/contracts/` for JSON shapes.
