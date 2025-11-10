"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import engine
from .models import Base
from .routers import auth as auth_router
from .routers import bots as bots_router
from .routers import replays as replays_router

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Exploding Kitten Arena API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(bots_router.router)
app.include_router(replays_router.router)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


__all__ = ["app"]
