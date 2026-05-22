"""
Health check endpoints
"""

from fastapi import APIRouter
import time

router = APIRouter()

# Track startup time
STARTUP_TIME = time.time()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns API status and version info
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "physics_engine": "operational",
        "uptime_seconds": time.time() - STARTUP_TIME
    }


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}
