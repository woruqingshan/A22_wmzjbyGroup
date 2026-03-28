from fastapi import APIRouter, HTTPException

from models import TranscribeRequest, TranscribeResponse
from services.asr_runtime import speech_runtime

router = APIRouter()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(request: TranscribeRequest) -> TranscribeResponse:
    if not request.audio_base64 and not request.user_text.strip() and not request.client_asr_text:
        raise HTTPException(status_code=400, detail="Speech service requires audio or transcript hints.")
    return speech_runtime.transcribe(request)
