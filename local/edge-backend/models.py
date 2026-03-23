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


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None)
    turn_id: int | None = Field(default=None, ge=1)
    user_text: str | None = Field(default=None)
    input_type: str = Field(default="text")
    client_ts: int | None = None
    audio_base64: str | None = None
    audio_format: str | None = None
    audio_duration_ms: int | None = Field(default=None, ge=0)


class RemoteChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    turn_id: int = Field(..., ge=1)
    user_text: str = Field(..., min_length=1)
    input_type: str = Field(default="text")
    client_ts: int | None = None
    audio_base64: str | None = None
    audio_format: str | None = None
    audio_duration_ms: int | None = Field(default=None, ge=0)


class AvatarAction(AvatarActionSchema):
    pass


class ChatResponse(ChatResponseSchema):
    avatar_action: AvatarAction


class ErrorResponse(ErrorResponseSchema):
    pass


class HealthResponse(BaseModel):
    status: str
    cloud_api_base: str
    request_timeout_seconds: float
