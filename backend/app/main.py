"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import engine
from .models import Base
from .routers import auth as auth_router
from .routers import bots as bots_router
from .routers import replays as replays_router

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Exploding Kitten Arena API", version="0.1.0")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions and ensure CORS headers are present."""
    # Get the origin from the request
    origin = request.headers.get("origin", "")
    
    # Check if the origin is allowed
    allowed = False
    if settings.allowed_origins:
        if "*" in settings.allowed_origins:
            allowed = True
        elif origin in settings.allowed_origins:
            allowed = True
    
    # Create the error response
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
    
    # Add CORS headers if origin is allowed
    if allowed:
        response.headers["Access-Control-Allow-Origin"] = origin if origin and "*" not in settings.allowed_origins else "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


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
