from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="A22 Orchestrator", version="0.1.0")


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    turn_id: int = Field(..., ge=1)
    user_text: str = Field(..., min_length=1)
    input_type: str = Field(default="text")
    client_ts: int | None = None


class AvatarAction(BaseModel):
    facial_expression: str
    head_motion: str


class ChatResponse(BaseModel):
    server_status: str
    reply_text: str
    emotion_style: str
    avatar_action: AvatarAction
    server_ts: int | None = None


@app.get("/health")
def health():
    return {"status": "ok", "server_time": datetime.now(timezone.utc).isoformat()}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # v0: mock reply; replace with orchestration + LLM/RAG later.
    return ChatResponse(
        server_status="ok",
        reply_text="你好，我收到你的消息了。当前为 orchestrator v0 固定回复。",
        emotion_style="gentle",
        avatar_action=AvatarAction(
            facial_expression="soft_concern",
            head_motion="slow_nod",
        ),
        server_ts=int(datetime.now(timezone.utc).timestamp()),
    )
