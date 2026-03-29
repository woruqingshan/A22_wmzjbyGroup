import os


class Settings:
    def __init__(self) -> None:
        self.asr_provider = os.getenv("ASR_PROVIDER", "qwen3_asr").strip().lower() or "qwen3_asr"
        self.asr_model = (
            os.getenv(
                "ASR_MODEL",
                "Qwen/Qwen3-ASR-0.6B",
            ).strip()
            or "Qwen/Qwen3-ASR-0.6B"
        )
        self.asr_language = os.getenv("ASR_LANGUAGE", "zh").strip() or "zh"
        self.asr_device = os.getenv("ASR_DEVICE", "cuda:0").strip() or "cuda:0"
        self.asr_max_new_tokens = int(os.getenv("ASR_MAX_NEW_TOKENS", "512"))
        self.asr_max_inference_batch_size = int(os.getenv("ASR_MAX_INFERENCE_BATCH_SIZE", "16"))
        self.asr_warmup_enabled = os.getenv("ASR_WARMUP_ENABLED", "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.tmp_dir = os.getenv("TMP_DIR", "/data/zifeng/siyuan/A22/tmp/speech").strip() or "/data/zifeng/siyuan/A22/tmp/speech"


settings = Settings()
