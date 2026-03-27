from pydantic import BaseModel, Field


class AudioMetaSchema(BaseModel):
    format: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    sample_rate_hz: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)
    source: str | None = None
    frame_count: int | None = Field(default=None, ge=0)


class SpeechFeaturesSchema(BaseModel):
    transcript_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    speaking_rate: float | None = Field(default=None, ge=0.0)
    pause_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    rms_energy: float | None = Field(default=None, ge=0.0)
    peak_level: float | None = Field(default=None, ge=0.0)
    pitch_hz: float | None = Field(default=None, ge=0.0)
    dominant_channel: int | None = Field(default=None, ge=1)
    emotion_tags: list[str] = Field(default_factory=list)
    channel_rms_levels: list[float] = Field(default_factory=list)
    source: str | None = None


class VisionFeaturesSchema(BaseModel):
    scene_summary: str | None = None
    attention_target: str | None = None
    motion_level: str | None = None
    emotion_tags: list[str] = Field(default_factory=list)


class ChatRequestSchema(BaseModel):
    session_id: str = Field(..., min_length=1)
    turn_id: int = Field(..., ge=1)
    user_text: str = Field(default="")
    input_type: str = Field(default="text")
    client_ts: int | None = None
    text_source: str | None = None
    client_asr_text: str | None = None
    client_asr_source: str | None = None
    audio_base64: str | None = None
    audio_format: str | None = None
    audio_duration_ms: int | None = Field(default=None, ge=0)
    audio_sample_rate_hz: int | None = Field(default=None, ge=1)
    audio_channels: int | None = Field(default=None, ge=1)
    audio_meta: AudioMetaSchema | None = None
    speech_features: SpeechFeaturesSchema | None = None
    vision_features: VisionFeaturesSchema | None = None
    alignment_mode: str | None = None


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
    alignment_mode: str | None = None


class ErrorResponseSchema(BaseModel):
    detail: str
