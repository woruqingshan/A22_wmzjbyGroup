import time
from datetime import datetime, timezone

from adapters.avatar_client import avatar_client
from adapters.llm_client import LLMRequest, llm_client
from adapters.speech_client import speech_client
from adapters.vision_client import vision_client
from config import settings
from models import ChatRequest, ChatResponse
from services.alignment import multimodal_alignment_service
from services.observability import orchestrator_observability
from services.policy_service import policy_service
from services.prompt_builder import prompt_builder
from services.session_state import session_state


class DialogService:
    async def build_reply(self, request: ChatRequest) -> ChatResponse:
        started_at = time.perf_counter()
        speech_result = await speech_client.analyze_turn(request)
        enriched_request = self._merge_request(
            request,
            user_text=speech_result.transcript_text,
            text_source=speech_result.text_source,
            audio_meta=speech_result.audio_meta,
            speech_features=speech_result.speech_features,
        )
        vision_features = await vision_client.extract_features(enriched_request)
        enriched_request = self._merge_request(
            enriched_request,
            vision_features=vision_features,
        )
        transcript = speech_result.transcript_text
        if not transcript:
            transcript = "The client sent an empty turn."

        aligned_turn = multimodal_alignment_service.align(enriched_request, transcript)
        orchestrator_observability.log_alignment_ready(
            request.session_id,
            request.turn_id,
            {
                "alignment_mode": aligned_turn.alignment_mode,
                "alignment_summary": aligned_turn.alignment_summary,
                "speech_context_ready": bool(aligned_turn.speech_context),
                "vision_context_ready": bool(aligned_turn.vision_context),
            },
        )
        context_messages = session_state.build_context_messages(request.session_id)
        memory_summary = session_state.get_summary(request.session_id)
        system_prompt = prompt_builder.build_system_prompt(
            settings.system_prompt,
            context_summary=memory_summary,
        )
        emotion_style = policy_service.select_emotion_style(enriched_request, transcript)
        avatar_action = policy_service.select_avatar_action(enriched_request, transcript)
        llm_result = await llm_client.generate_reply(
            LLMRequest(
                session_id=request.session_id,
                turn_id=request.turn_id,
                system_prompt=system_prompt,
                user_text=aligned_turn.llm_user_text,
                input_mode=enriched_request.input_type,
                context_messages=context_messages,
                context_summary=memory_summary,
            )
        )
        avatar_generation = await avatar_client.generate(
            request=enriched_request,
            reply_text=llm_result.reply_text,
            emotion_style=emotion_style,
            avatar_action=avatar_action,
        )

        session_state.append_message(
            request.session_id,
            role="user",
            content=aligned_turn.canonical_user_text,
            turn_id=request.turn_id,
            input_mode=request.input_type,
        )
        session_state.append_message(
            request.session_id,
            role="assistant",
            content=llm_result.reply_text,
            turn_id=request.turn_id,
            input_mode="text",
        )

        response = ChatResponse(
            server_status="ok",
            reply_text=llm_result.reply_text,
            emotion_style=emotion_style,
            avatar_action=avatar_action,
            avatar_output=avatar_generation.avatar_output,
            server_ts=int(datetime.now(timezone.utc).timestamp()),
            input_mode=enriched_request.input_type,
            reply_audio_url=avatar_generation.reply_audio_url,
            response_source=llm_result.response_source,
            context_summary=memory_summary or None,
            reasoning_hint=llm_result.reasoning_hint
            or aligned_turn.alignment_summary
            or prompt_builder.build_reasoning_hint(context_messages),
            turn_time_window=enriched_request.turn_time_window,
            alignment_mode=aligned_turn.alignment_mode,
        )
        orchestrator_observability.log_chat_response(
            request.session_id,
            request.turn_id,
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            payload={
                "response_source": response.response_source,
                "alignment_mode": response.alignment_mode,
                "emotion_style": response.emotion_style,
                "reply_text_preview": response.reply_text[:200],
            },
        )
        return response

    def _merge_request(self, request: ChatRequest, **updates) -> ChatRequest:
        normalized_updates = {key: value for key, value in updates.items()}
        if hasattr(request, "model_copy"):
            return request.model_copy(update=normalized_updates)
        return request.copy(update=normalized_updates)


dialog_service = DialogService()
