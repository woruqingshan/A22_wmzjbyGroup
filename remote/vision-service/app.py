from fastapi import FastAPI

from routes.extract import router as extract_router
from routes.health import router as health_router

app = FastAPI(title="A22 Vision Service", version="0.1.0")
app.include_router(health_router)
app.include_router(extract_router)
