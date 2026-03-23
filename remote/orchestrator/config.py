import os


class Settings:
    def __init__(self) -> None:
        self.llm_provider = os.getenv("LLM_PROVIDER", "mock").strip().lower() or "mock"
        self.llm_model = os.getenv("LLM_MODEL", "mock-support-v1").strip() or "mock-support-v1"
        self.max_context_messages = int(os.getenv("MAX_CONTEXT_MESSAGES", "8"))
        self.context_summary_turns = int(os.getenv("CONTEXT_SUMMARY_TURNS", "4"))
        self.system_prompt = os.getenv(
            "LLM_SYSTEM_PROMPT",
            (
                "You are A22, an emotionally supportive digital human assistant. "
                "Answer with warmth, empathy, and concise helpful guidance. "
                "Keep replies safe, supportive, and suitable for a local demo."
            ),
        ).strip()


settings = Settings()
