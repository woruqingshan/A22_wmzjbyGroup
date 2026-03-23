import sys
from pathlib import Path

from pydantic import BaseModel, Field

SHARED_PATH_CANDIDATES = [
    Path("/shared"),
    Path(__file__).resolve().parents[2] / "shared" if len(Path(__file__).resolve().parents) > 2 else None,
]

for candidate in SHARED_PATH_CANDIDATES:
    if candidate and candidate.exists() and str(candidate) not in sys.path:
        sys.path.append(str(candidate))

from contracts.schemas import (  # noqa: E402
    AvatarActionSchema,
    ChatRequestSchema,
    ChatResponseSchema,
    ErrorResponseSchema,
)


class ChatRequest(ChatRequestSchema):
    pass


class ContextMessage(BaseModel):
    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    turn_id: int | None = Field(default=None, ge=1)
    input_mode: str | None = None


class AvatarAction(AvatarActionSchema):
    pass


class ChatResponse(ChatResponseSchema):
    avatar_action: AvatarAction
    reply_audio_url: str | None = None


class HealthResponse(BaseModel):
    status: str
    server_time: str
    orchestrator_mode: str
    llm_provider: str
    llm_model: str


class ErrorResponse(ErrorResponseSchema):
    pass
