from fastapi import FastAPI

from routes.generate import router as generate_router
from routes.health import router as health_router

app = FastAPI(title="A22 Avatar Service", version="0.1.0")
app.include_router(health_router)
app.include_router(generate_router)
