import os


class Settings:
    def __init__(self) -> None:
        self.tmp_dir = os.getenv("TMP_DIR", "/data/zifeng/siyuan/A22/tmp/vision").strip() or "/data/zifeng/siyuan/A22/tmp/vision"
        self.extractor_mode = os.getenv("VISION_EXTRACTOR_MODE", "metadata_placeholder").strip().lower() or "metadata_placeholder"
        self.vision_model = (
            os.getenv(
                "VISION_MODEL",
                "/data/zifeng/siyuan/A22/models/Qwen2.5-VL-7B-Instruct",
            ).strip()
            or "/data/zifeng/siyuan/A22/models/Qwen2.5-VL-7B-Instruct"
        )
        self.vision_device = os.getenv("VISION_DEVICE", "cuda:1").strip() or "cuda:1"
        self.frame_input_mode = os.getenv("VISION_FRAME_INPUT_MODE", "event_window_keyframes").strip().lower() or "event_window_keyframes"


settings = Settings()
