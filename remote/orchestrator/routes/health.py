from datetime import datetime, timezone

from fastapi import APIRouter

from config import settings
from models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        server_time=datetime.now(timezone.utc).isoformat(),
        orchestrator_mode="llm-adapter-ready",
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
    )
