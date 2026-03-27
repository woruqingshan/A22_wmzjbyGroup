import os


class Settings:
    def __init__(self) -> None:
        self.llm_provider = os.getenv("LLM_PROVIDER", "mock").strip().lower() or "mock"
        self.llm_model = os.getenv("LLM_MODEL", "mock-support-v1").strip() or "mock-support-v1"

        self.llm_api_base = os.getenv("LLM_API_BASE", "http://127.0.0.1:8000/v1").strip().rstrip("/")
        self.llm_api_key = os.getenv("LLM_API_KEY", "EMPTY").strip() or "EMPTY"
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.4"))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "256"))
        self.llm_request_timeout_seconds = int(os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "60"))

        self.max_context_messages = int(os.getenv("MAX_CONTEXT_MESSAGES", "8"))
        self.context_summary_turns = int(os.getenv("CONTEXT_SUMMARY_TURNS", "4"))
        self.log_dir = os.getenv("LOG_DIR", "/tmp/a22_logs/orchestrator").strip() or "/tmp/a22_logs/orchestrator"
        self.system_prompt = os.getenv(
            "LLM_SYSTEM_PROMPT",
            (
                "You are A22, an emotionally supportive digital human assistant. "
                "Answer with warmth, empathy, and concise helpful guidance. "
                "Keep replies safe, supportive, and suitable for a local demo."
            ),
        ).strip()


settings = Settings()
