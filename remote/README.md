# remote

Services that run on the **lab server** or other remote hosts: orchestration, LLM, RAG, TTS, etc.

## Current layout

- `orchestrator/` — v0 HTTP API matching `shared/contracts/api_v1.md`.

Deploy with Python venv or Docker; see `orchestrator/README.md` and root `compose.remote.yaml`.
