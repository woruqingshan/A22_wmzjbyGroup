from dataclasses import dataclass, field


@dataclass
class AudioMeta:
    format: str | None = None
    duration_ms: int | None = None
    sample_rate_hz: int | None = None
    channels: int | None = None
    source: str | None = None
    frame_count: int | None = None


@dataclass
class SpeechFeatures:
    transcript_confidence: float | None = None
    speaking_rate: float | None = None
    pause_ratio: float | None = None
    rms_energy: float | None = None
    peak_level: float | None = None
    pitch_hz: float | None = None
    dominant_channel: int | None = None
    emotion_tags: list[str] = field(default_factory=list)
    channel_rms_levels: list[float] = field(default_factory=list)
    source: str | None = None


@dataclass
class TranscriptionResult:
    text: str
    source: str
    confidence: float | None = None


@dataclass
class ProcessedAudioTurn:
    user_text: str
    text_source: str
    alignment_mode: str
    audio_meta: AudioMeta
    speech_features: SpeechFeatures
