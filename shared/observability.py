import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


def build_run_id(service_name: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{service_name}-{timestamp}-{uuid.uuid4().hex[:8]}"


def sanitize_payload(value: Any, *, max_text_length: int = 2000) -> Any:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    elif hasattr(value, "dict"):
        value = value.dict()

    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if key.endswith("_base64") and isinstance(item, str):
                sanitized[key] = f"<redacted:{len(item)} chars>"
                continue
            sanitized[key] = sanitize_payload(item, max_text_length=max_text_length)
        return sanitized

    if isinstance(value, list):
        return [sanitize_payload(item, max_text_length=max_text_length) for item in value]

    if isinstance(value, str) and len(value) > max_text_length:
        return f"{value[:max_text_length]}...<truncated:{len(value) - max_text_length} chars>"

    return value


class JsonlRunLogger:
    def __init__(
        self,
        *,
        service_name: str,
        log_dir: str,
        channel: str,
        run_id: str,
    ) -> None:
        self.service_name = service_name
        self.channel = channel
        self.run_id = run_id
        self.log_dir = Path(log_dir).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.log_dir / f"{service_name}-{channel}-{run_id}.jsonl"
        self._lock = Lock()

    def emit(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "service": self.service_name,
            "channel": self.channel,
            "run_id": self.run_id,
            "event_type": event_type,
            "payload": sanitize_payload(payload),
        }

        with self._lock:
            with self.file_path.open("a", encoding="utf-8") as output_file:
                output_file.write(json.dumps(record, ensure_ascii=False, default=str))
                output_file.write("\n")

        return record
