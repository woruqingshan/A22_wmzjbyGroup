# API contract v0

Version: **v0** (frozen for local and remote skeleton; breaking changes require a new version file).

## Scope

- Describes the JSON shape between **local `edge-backend`** and **remote `orchestrator`** over HTTP.
- Frontend may send a compatible subset; `edge-backend` is responsible for normalization before calling remote.

## Endpoints (orchestrator)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness and minimal status. |
| POST | `/chat` | Turn-based user message in, structured reply out. |

## Request: `POST /chat`

Content-Type: `application/json`

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | yes | Stable session identifier for server-side context. |
| `turn_id` | integer | yes | Monotonic turn index within the session. |
| `user_text` | string | yes | User utterance text for this turn. |
| `input_type` | string | yes | e.g. `text`, reserved for future `audio` / `multimodal`. |
| `client_ts` | integer | no | Unix epoch seconds from client when the turn was created. |

### Example

See `chat_request.example.json`.

## Response: `POST /chat` (200)

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_status` | string | yes | e.g. `ok`, `error`. |
| `reply_text` | string | yes | Natural language reply to show in UI. |
| `emotion_style` | string | yes | High-level style hint for rendering. |
| `avatar_action` | object | yes | Structured hints for digital human layer. |
| `avatar_action.facial_expression` | string | yes | Expression token. |
| `avatar_action.head_motion` | string | yes | Head motion token. |
| `server_ts` | integer | no | Unix epoch seconds on server when the reply was produced. |

### Example

See `chat_response.example.json`.

## Health: `GET /health`

### Response (200)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `ok` when service is up. |

Optional: `server_time` ISO8601 string for debugging.

## Notes

- Keep payloads small: avoid sending full dialog history every turn once server-side session store exists.
- Do not embed large debug blobs in responses intended for the UI path.
