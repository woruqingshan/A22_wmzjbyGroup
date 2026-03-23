from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field
import os

app = FastAPI(title="A22 Edge Backend", version="0.1.0")


class ChatRequest(BaseModel):
    session_id: str = Field(default="demo-001", min_length=1)
    turn_id: int = Field(default=1, ge=1)
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
    return {
        "status": "ok",
        "cloud_api_base": os.getenv("CLOUD_API_BASE", ""),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # v0: local mock; replace with httpx call to CLOUD_API_BASE + /chat when remote is wired.
    return ChatResponse(
        server_status="ok",
        reply_text=f"edge-backend (local mock) received: {req.user_text}",
        emotion_style="gentle",
        avatar_action=AvatarAction(
            facial_expression="neutral",
            head_motion="none",
        ),
        server_ts=int(datetime.now(timezone.utc).timestamp()),
    )
