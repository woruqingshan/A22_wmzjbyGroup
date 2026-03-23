from pydantic import BaseModel, Field


class ChatRequestSchema(BaseModel):
    session_id: str = Field(..., min_length=1)
    turn_id: int = Field(..., ge=1)
    user_text: str = Field(default="")
    input_type: str = Field(default="text")
    client_ts: int | None = None
    audio_base64: str | None = None
    audio_format: str | None = None
    audio_duration_ms: int | None = Field(default=None, ge=0)


class AvatarActionSchema(BaseModel):
    facial_expression: str
    head_motion: str


class ChatResponseSchema(BaseModel):
    server_status: str
    reply_text: str
    emotion_style: str
    avatar_action: AvatarActionSchema
    server_ts: int | None = None
    input_mode: str | None = None
    response_source: str | None = None
    context_summary: str | None = None
    reasoning_hint: str | None = None


class ErrorResponseSchema(BaseModel):
    detail: str
