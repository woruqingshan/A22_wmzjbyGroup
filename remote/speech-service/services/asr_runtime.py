import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from config import settings
from models import AudioMeta, SpeechFeatures, TranscribeRequest, TranscribeResponse
from services.feature_extractor import audio_feature_extractor
from services.storage import speech_storage
from services.wav_utils import decode_audio_base64, decode_wav_audio


class SpeechRuntime:
    def __init__(self) -> None:
        self._pipeline = None

    def _ensure_pipeline(self):
        if self._pipeline is not None:
            return self._pipeline

        try:
            import torch
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Speech service requires torch and transformers.") from exc

        model_ref = settings.asr_model
        model_path = Path(model_ref)
        local_files_only = model_path.exists()
        torch_dtype = torch.float16 if settings.asr_device.startswith("cuda") else torch.float32

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_ref,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
            local_files_only=local_files_only,
        )
        model.to(settings.asr_device)

        processor = AutoProcessor.from_pretrained(
            model_ref,
            local_files_only=local_files_only,
        )
        self._pipeline = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=settings.asr_device,
        )
        self._pipeline.model.config.forced_decoder_ids = (
            self._pipeline.tokenizer.get_decoder_prompt_ids(
                language=settings.asr_language,
                task="transcribe",
            )
        )
        return self._pipeline

    def warmup(self) -> None:
        if not settings.asr_warmup_enabled:
            return

        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Speech service requires numpy.") from exc

        pipeline_instance = self._ensure_pipeline()
        pipeline_instance(
            {
                "raw": np.zeros(48000, dtype=np.float32),
                "sampling_rate": 48000,
            },
            generate_kwargs={"language": settings.asr_language, "task": "transcribe"},
        )

    def transcribe(self, request: TranscribeRequest) -> TranscribeResponse:
        if request.user_text.strip() and not request.audio_base64:
            return TranscribeResponse(
                transcript_text=request.user_text.strip(),
                text_source="upstream_text",
                transcript_confidence=1.0,
                audio_meta=request.audio_meta,
                speech_features=request.audio_meta and SpeechFeatures(source="upstream_text_only") or None,
                model_ref=settings.asr_model,
                device=settings.asr_device,
            )

        if not request.audio_base64:
            transcript_text = (request.client_asr_text or request.user_text or "").strip()
            return TranscribeResponse(
                transcript_text=transcript_text or "",
                text_source=request.client_asr_source or "speech_service_placeholder",
                transcript_confidence=0.5 if transcript_text else 0.1,
                audio_meta=request.audio_meta,
                speech_features=SpeechFeatures(source="hint_only_speech_features"),
                model_ref=settings.asr_model,
                device=settings.asr_device,
            )

        audio_bytes = decode_audio_base64(request.audio_base64)
        normalized_format = (request.audio_format or "wav").strip().lower() or "wav"
        base_audio_meta = request.audio_meta or AudioMeta(
            format=normalized_format,
            duration_ms=request.audio_duration_ms,
            sample_rate_hz=request.audio_sample_rate_hz,
            channels=request.audio_channels,
            source="remote_speech_service",
        )

        speech_storage.persist_audio(
            session_id=request.session_id,
            turn_id=request.turn_id,
            audio_bytes=audio_bytes,
            audio_format=normalized_format,
        )

        transcript_text = self._run_asr(audio_bytes, base_audio_meta)

        decoded_audio = None
        if normalized_format == "wav":
            try:
                decoded_audio = decode_wav_audio(audio_bytes)
            except ValueError:
                decoded_audio = None

        if decoded_audio is not None:
            audio_meta, speech_features = audio_feature_extractor.extract(
                decoded_audio,
                audio_format=normalized_format,
                transcript=transcript_text,
                transcript_confidence=None,
            )
            audio_meta.source = "remote_speech_service"
            speech_features.source = "remote_speech_service"
        else:
            audio_meta = base_audio_meta
            speech_features = SpeechFeatures(
                transcript_confidence=None,
                emotion_tags=["steady"],
                source="remote_speech_service_metadata_only",
            )

        response = TranscribeResponse(
            transcript_text=transcript_text,
            text_source="remote_belle_whisper",
            transcript_confidence=None,
            audio_meta=audio_meta,
            speech_features=speech_features,
            model_ref=settings.asr_model,
            device=settings.asr_device,
        )
        serialized_response = response.model_dump() if hasattr(response, "model_dump") else response.dict()
        speech_storage.persist_transcription(
            session_id=request.session_id,
            turn_id=request.turn_id,
            payload=json.loads(json.dumps(serialized_response, ensure_ascii=False, default=str)),
        )
        return response

    def _run_asr(self, audio_bytes: bytes, audio_meta: AudioMeta) -> str:
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Speech service requires numpy.") from exc

        pipeline_instance = self._ensure_pipeline()
        generate_kwargs = {"language": settings.asr_language, "task": "transcribe"}

        if (audio_meta.format or "wav").lower() == "wav":
            decoded_audio = decode_wav_audio(audio_bytes)
            if decoded_audio.channels == 1:
                waveform = decoded_audio.samples_by_channel[0]
            else:
                waveform = [
                    sum(channel_samples) / decoded_audio.channels
                    for channel_samples in zip(*decoded_audio.samples_by_channel, strict=False)
                ]
            pipeline_input = {
                "raw": np.asarray(waveform, dtype=np.float32),
                "sampling_rate": decoded_audio.sample_rate_hz,
            }
            result = pipeline_instance(pipeline_input, generate_kwargs=generate_kwargs)
        else:
            suffix = f".{(audio_meta.format or 'wav').lower()}"
            with NamedTemporaryFile(suffix=suffix) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio.flush()
                result = pipeline_instance(temp_audio.name, generate_kwargs=generate_kwargs)

        if isinstance(result, dict):
            text = str(result.get("text", "")).strip()
        else:
            text = str(result).strip()

        return text or "Audio input received from the remote speech service."


speech_runtime = SpeechRuntime()
