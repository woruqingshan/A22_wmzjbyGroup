import os


class Settings:
    def __init__(self) -> None:
        self.avatar_id = os.getenv("AVATAR_ID", "default-2d").strip() or "default-2d"
        self.renderer_mode = os.getenv("AVATAR_RENDERER_MODE", "parameterized_2d").strip() or "parameterized_2d"
        self.transport_mode = os.getenv("AVATAR_TRANSPORT_MODE", "http_poll").strip() or "http_poll"
        self.websocket_endpoint = os.getenv("AVATAR_WEBSOCKET_ENDPOINT", "/ws/avatar").strip() or "/ws/avatar"
        self.tmp_dir = os.getenv("TMP_DIR", "/data/zifeng/siyuan/A22/tmp/avatar").strip() or "/data/zifeng/siyuan/A22/tmp/avatar"
        self.tts_mode = os.getenv("TTS_MODE", "placeholder").strip().lower() or "placeholder"
        self.tts_model = (
            os.getenv(
                "TTS_MODEL",
                "/data/zifeng/siyuan/A22/models/CosyVoice2-0.5B",
            ).strip()
            or "/data/zifeng/siyuan/A22/models/CosyVoice2-0.5B"
        )
        self.tts_device = os.getenv("TTS_DEVICE", "cuda:1").strip() or "cuda:1"


settings = Settings()
