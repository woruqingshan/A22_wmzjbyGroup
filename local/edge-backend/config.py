import os


class Settings:
    def __init__(self) -> None:
        cloud_api_base = os.getenv("CLOUD_API_BASE", "http://127.0.0.1:19000").strip()
        self.cloud_api_base = cloud_api_base.rstrip("/")
        self.request_timeout_seconds = float(os.getenv("REMOTE_TIMEOUT_SECONDS", "15"))
        self.log_dir = os.getenv("LOG_DIR", "/logs")
        self.data_dir = os.getenv("DATA_DIR", "/data")
        self.default_session_prefix = os.getenv("DEFAULT_SESSION_PREFIX", "local-session")
        self.audio_pipeline_role = (
            os.getenv("AUDIO_PIPELINE_ROLE", "remote_forward_only").strip().lower() or "remote_forward_only"
        )
        self.local_video_frame_limit = max(1, int(os.getenv("LOCAL_VIDEO_FRAME_LIMIT", "3")))
        self.local_video_max_dimension = max(64, int(os.getenv("LOCAL_VIDEO_MAX_DIMENSION", "640")))


settings = Settings()
