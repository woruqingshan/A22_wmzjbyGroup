from tempfile import NamedTemporaryFile
from typing import Protocol

from config import settings
from services.audio.contracts import AudioMeta, TranscriptionResult


class BaseSpeechRecognizer(Protocol):
    provider_name: str

    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        audio_meta: AudioMeta,
        client_text_hint: str | None,
        client_text_source: str | None,
    ) -> TranscriptionResult:
        ...


class BrowserHintSpeechRecognizer:
    provider_name = "browser_hint"

    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        audio_meta: AudioMeta,
        client_text_hint: str | None,
        client_text_source: str | None,
    ) -> TranscriptionResult:
        del audio_bytes, audio_meta

        if client_text_hint and client_text_hint.strip():
            return TranscriptionResult(
                text=client_text_hint.strip(),
                source=client_text_source or "browser_speech_api",
                confidence=0.65,
            )

        return TranscriptionResult(
            text="Audio input received from the local microphone.",
            source="audio_placeholder",
            confidence=0.15,
        )


class FasterWhisperSpeechRecognizer:
    provider_name = "faster_whisper"

    def __init__(self) -> None:
        self._model = None

    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        audio_meta: AudioMeta,
        client_text_hint: str | None,
        client_text_source: str | None,
    ) -> TranscriptionResult:
        del client_text_hint, client_text_source

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("faster_whisper is not installed in the local edge-backend environment.") from exc

        if self._model is None:
            self._model = WhisperModel(
                settings.local_asr_model,
                device=settings.local_asr_device,
                compute_type=settings.local_asr_compute_type,
            )

        suffix = f".{(audio_meta.format or 'wav').lower()}"
        with NamedTemporaryFile(suffix=suffix) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio.flush()
            segments, info = self._model.transcribe(
                temp_audio.name,
                language=settings.local_asr_language or None,
                vad_filter=True,
            )
            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()

        if not text:
            return TranscriptionResult(
                text="Audio input received from the local microphone.",
                source="audio_placeholder",
                confidence=0.1,
            )

        probability = getattr(info, "language_probability", None)
        return TranscriptionResult(
            text=text,
            source="faster_whisper",
            confidence=round(probability, 4) if isinstance(probability, float) else None,
        )


class FallbackSpeechRecognizer:
    provider_name = "fallback"

    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        audio_meta: AudioMeta,
        client_text_hint: str | None,
        client_text_source: str | None,
    ) -> TranscriptionResult:
        del audio_bytes, audio_meta, client_text_source

        if client_text_hint and client_text_hint.strip():
            return TranscriptionResult(
                text=client_text_hint.strip(),
                source="browser_hint_fallback",
                confidence=0.5,
            )

        return TranscriptionResult(
            text="Audio input received from the local microphone.",
            source="audio_placeholder",
            confidence=0.1,
        )


class SpeechRecognitionService:
    def __init__(self) -> None:
        self._provider_name = settings.local_asr_provider
        self._provider = self._build_provider()
        self._fallback = FallbackSpeechRecognizer()

    def _build_provider(self) -> BaseSpeechRecognizer:
        if settings.local_asr_provider == "faster_whisper":
            return FasterWhisperSpeechRecognizer()

        if settings.local_asr_provider == "fallback":
            return FallbackSpeechRecognizer()

        return BrowserHintSpeechRecognizer()

    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        audio_meta: AudioMeta,
        client_text_hint: str | None,
        client_text_source: str | None,
    ) -> TranscriptionResult:
        try:
            return self._provider.transcribe(
                audio_bytes=audio_bytes,
                audio_meta=audio_meta,
                client_text_hint=client_text_hint,
                client_text_source=client_text_source,
            )
        except Exception:  # noqa: BLE001
            return self._fallback.transcribe(
                audio_bytes=audio_bytes,
                audio_meta=audio_meta,
                client_text_hint=client_text_hint,
                client_text_source=client_text_source,
            )


speech_recognition_service = SpeechRecognitionService()
