from typing import Protocol

from config import settings
from models import ContextMessage


class LLMRequest:
    def __init__(
        self,
        *,
        session_id: str,
        turn_id: int,
        system_prompt: str,
        user_text: str,
        input_mode: str,
        context_messages: list[ContextMessage],
        context_summary: str,
    ) -> None:
        self.session_id = session_id
        self.turn_id = turn_id
        self.system_prompt = system_prompt
        self.user_text = user_text
        self.input_mode = input_mode
        self.context_messages = context_messages
        self.context_summary = context_summary


class LLMResult:
    def __init__(
        self,
        *,
        reply_text: str,
        response_source: str,
        reasoning_hint: str | None = None,
    ) -> None:
        self.reply_text = reply_text
        self.response_source = response_source
        self.reasoning_hint = reasoning_hint


class BaseLLMProvider(Protocol):
    provider_name: str

    async def complete(self, request: LLMRequest) -> LLMResult:
        ...


class MockLLMProvider:
    provider_name = "mock"

    async def complete(self, request: LLMRequest) -> LLMResult:
        lowered = request.user_text.lower()

        if any(keyword in lowered for keyword in ["sad", "unhappy", "压力", "焦虑", "难过", "不开心"]):
            return LLMResult(
                reply_text="我在这里陪着你。你可以慢慢说，我会先认真听你现在最在意的事情。",
                response_source="mock",
                reasoning_hint="detected-emotional-keywords",
            )

        if request.input_mode == "audio":
            return LLMResult(
                reply_text="我已经收到你的语音输入了。当前先用 mock LLM 回复，下一阶段会接入真实 ASR 和更完整的情绪理解。",
                response_source="mock",
                reasoning_hint="audio-placeholder",
            )

        if request.context_summary:
            return LLMResult(
                reply_text=f"我记得你刚刚提到过：{request.context_summary}。这次我继续陪你往下聊。",
                response_source="mock",
                reasoning_hint="summary-conditioned-response",
            )

        return LLMResult(
            reply_text="你好，我已经收到你的消息了。当前是 remote orchestrator 的 mock LLM 回复。",
            response_source="mock",
            reasoning_hint="default-mock-response",
        )


class FallbackLLMProvider:
    provider_name = "mock-fallback"

    def __init__(self, configured_provider: str) -> None:
        self.configured_provider = configured_provider
        self._delegate = MockLLMProvider()

    async def complete(self, request: LLMRequest) -> LLMResult:
        result = await self._delegate.complete(request)
        result.response_source = f"fallback:{self.configured_provider}"
        result.reasoning_hint = "unconfigured-provider-fallback"
        return result


class LLMClient:
    def __init__(self) -> None:
        self.provider_name = settings.llm_provider
        self.model_name = settings.llm_model
        self._provider = self._build_provider()

    def _build_provider(self) -> BaseLLMProvider:
        if settings.llm_provider == "mock":
            return MockLLMProvider()

        # Keep the adapter provider-neutral now and fall back until a real provider is configured.
        return FallbackLLMProvider(settings.llm_provider)

    async def generate_reply(self, request: LLMRequest) -> LLMResult:
        return await self._provider.complete(request)


llm_client = LLMClient()
