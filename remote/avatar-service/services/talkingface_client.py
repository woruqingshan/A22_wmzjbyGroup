import json
from dataclasses import dataclass
from urllib import error, request

from config import settings


@dataclass
class TalkingfaceResult:
    video_url: str | None
    duration_ms: int | None = None
    fps: float | None = None
    width: int | None = None
    height: int | None = None
    mime_type: str | None = None


class TalkingfaceClient:
    def generate(
        self,
        *,
        session_id: str,
        turn_id: int,
        audio_url: str | None,
        reply_text: str,
        emotion_style: str,
    ) -> TalkingfaceResult:
        if not settings.talkingface_enabled:
            return TalkingfaceResult(video_url=None)
        if not audio_url:
            return TalkingfaceResult(video_url=None)

        payload = {
            "provider": settings.talkingface_provider,
            "session_id": session_id,
            "turn_id": turn_id,
            "audio_url": audio_url,
            "reply_text": reply_text,
            "emotion_style": emotion_style,
            "avatar_ref": settings.talkingface_avatar_ref or None,
            "pose": settings.talkingface_pose,
        }

        url = f"{settings.talkingface_base}{settings.talkingface_generate_path}"
        req = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=settings.talkingface_timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, ValueError):
            return TalkingfaceResult(video_url=None)

        return TalkingfaceResult(
            video_url=body.get("video_url"),
            duration_ms=body.get("duration_ms"),
            fps=body.get("fps"),
            width=body.get("width"),
            height=body.get("height"),
            mime_type=body.get("mime_type") or "video/mp4",
        )


talkingface_client = TalkingfaceClient()
