import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from config import settings
from models import AudioMeta, SpeechFeatures, TranscribeRequest, TranscribeResponse
from services.feature_extractor import audio_feature_extractor
from services.storage import speech_storage
from services.wav_utils import decode_audio_base64, decode_wav_audio


class SpeechRuntime:
    def __init__(self) -> None:
        self._belle_pipeline = None
        self._qwen_model = None

    @staticmethod
    def _is_cuda_device(device: str) -> bool:
        return str(device).lower().startswith("cuda")

    @staticmethod
    def _normalize_provider(provider: str) -> str:
        normalized = (provider or "").strip().lower()
        if normalized in {"qwen3_asr", "qwen3-asr", "qwen_asr", "qwen"}:
            return "qwen3_asr"
        return "belle_whisper"

    def _ensure_belle_pipeline(self):
        if self._belle_pipeline is not None:
            return self._belle_pipeline

        try:
            import torch
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Speech service requires torch and transformers.") from exc

        model_ref = settings.asr_model
        model_path = Path(model_ref)
        local_files_only = model_path.exists()
        torch_dtype = torch.float16 if self._is_cuda_device(settings.asr_device) else torch.float32

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
        self._belle_pipeline = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=settings.asr_device,
        )
        self._belle_pipeline.model.config.forced_decoder_ids = (
            self._belle_pipeline.tokenizer.get_decoder_prompt_ids(
                language=settings.asr_language,
                task="transcribe",
            )
        )
        return self._belle_pipeline

    def _ensure_qwen_model(self):
        if self._qwen_model is not None:
            return self._qwen_model

        try:
            import torch
            from qwen_asr import Qwen3ASRModel
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Speech service requires qwen-asr for ASR_PROVIDER=qwen3_asr.") from exc

        model_ref = settings.asr_model
        model_path = Path(model_ref)
        local_files_only = model_path.exists()

        model_kwargs: dict[str, Any] = {
            "torch_dtype": torch.bfloat16 if self._is_cuda_device(settings.asr_device) else torch.float32,
            "device_map": "auto" if self._is_cuda_device(settings.asr_device) else settings.asr_device,
            "trust_remote_code": True,
        }
        if local_files_only:
            model_kwargs["local_files_only"] = True

        self._qwen_model = Qwen3ASRModel.from_pretrained(
            model_ref,
            max_inference_batch_size=settings.asr_max_inference_batch_size,
            max_new_tokens=settings.asr_max_new_tokens,
            **model_kwargs,
        )
        return self._qwen_model

    def _qwen_language(self) -> str | None:
        language = (settings.asr_language or "").strip()
        if not language:
            return None

        normalized = language.lower()
        language_map = {
            "zh": "Chinese",
            "zh-cn": "Chinese",
            "chinese": "Chinese",
            "en": "English",
            "english": "English",
            "ja": "Japanese",
            "japanese": "Japanese",
            "ko": "Korean",
            "korean": "Korean",
        }
        return language_map.get(normalized, language)

    @staticmethod
    def _extract_qwen_text(output: Any) -> str:
        if not output:
            return ""

        candidate = output[0] if isinstance(output, list) else output
        if hasattr(candidate, "text"):
            return str(candidate.text or "").strip()
        if isinstance(candidate, dict):
            return str(candidate.get("text", "")).strip()
        return str(candidate).strip()

    def warmup(self) -> None:
        if not settings.asr_warmup_enabled:
            return

        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Speech service requires numpy.") from exc

        provider = self._normalize_provider(settings.asr_provider)
        if provider == "qwen3_asr":
            qwen_model = self._ensure_qwen_model()
            qwen_model.transcribe(
                audio=(np.zeros(16000, dtype=np.float32), 16000),
                language=self._qwen_language(),
            )
            return

        pipeline_instance = self._ensure_belle_pipeline()
        pipeline_instance(
            {"raw": np.zeros(48000, dtype=np.float32), "sampling_rate": 48000},
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

        provider = self._normalize_provider(settings.asr_provider)
        text_source = "remote_qwen3_asr" if provider == "qwen3_asr" else "remote_belle_whisper"

        response = TranscribeResponse(
            transcript_text=transcript_text,
            text_source=text_source,
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
        provider = self._normalize_provider(settings.asr_provider)
        if provider == "qwen3_asr":
            return self._run_qwen_asr(audio_bytes, audio_meta)
        return self._run_belle_asr(audio_bytes, audio_meta)

    def _run_belle_asr(self, audio_bytes: bytes, audio_meta: AudioMeta) -> str:
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Speech service requires numpy.") from exc

        pipeline_instance = self._ensure_belle_pipeline()
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

    def _run_qwen_asr(self, audio_bytes: bytes, audio_meta: AudioMeta) -> str:
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Speech service requires numpy.") from exc

        qwen_model = self._ensure_qwen_model()
        forced_language = self._qwen_language()

        if (audio_meta.format or "wav").lower() == "wav":
            decoded_audio = decode_wav_audio(audio_bytes)
            if decoded_audio.channels == 1:
                waveform = decoded_audio.samples_by_channel[0]
            else:
                waveform = [
                    sum(channel_samples) / decoded_audio.channels
                    for channel_samples in zip(*decoded_audio.samples_by_channel, strict=False)
                ]
            qwen_input = (np.asarray(waveform, dtype=np.float32), decoded_audio.sample_rate_hz)
            result = qwen_model.transcribe(audio=qwen_input, language=forced_language)
        else:
            suffix = f".{(audio_meta.format or 'wav').lower()}"
            with NamedTemporaryFile(suffix=suffix) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio.flush()
                result = qwen_model.transcribe(audio=temp_audio.name, language=forced_language)

        text = self._extract_qwen_text(result)
        return text or "Audio input received from the remote speech service."


speech_runtime = SpeechRuntime()
