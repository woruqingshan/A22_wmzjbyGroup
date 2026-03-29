import logging

from fastapi import APIRouter, HTTPException

from models import TranscribeRequest, TranscribeResponse
from services.asr_runtime import speech_runtime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(request: TranscribeRequest) -> TranscribeResponse:
    if not request.audio_base64 and not request.user_text.strip() and not request.client_asr_text:
        raise HTTPException(status_code=400, detail="Speech service requires audio or transcript hints.")
    try:
        return speech_runtime.transcribe(request)
    except Exception as exc:
        logger.exception("speech runtime transcribe failed")
        raise HTTPException(status_code=500, detail=f"speech runtime error: {exc}") from exc
