"""
FastAPI application entry-point.

Run with:
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Buffalo Winter Elder Help Routing API - Phase 1 scaffold.",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    """
    Simple health endpoint confirming the service is running.
    """

    return {"status": "ok", "message": "Buffalo to the resuscue API is running."}


app.include_router(api_router)
