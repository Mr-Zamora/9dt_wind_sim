"""
AeroClass FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
from pathlib import Path

from routers import simulations, designs, health
from config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description="Educational aerodynamics simulation API for STEM classrooms",
    version=settings.api_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (API routes first)
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(simulations.router, prefix="/api/simulations", tags=["Simulations"])
app.include_router(designs.router, prefix="/api/designs", tags=["Designs"])

# Root endpoint
@app.get("/")
async def root():
    """Redirect to UI"""
    return RedirectResponse(url="/ui/index.html")

# Mount static files LAST (so API routes take precedence)
UI_PATH = settings.ui_path_obj
print(f"UI Path: {UI_PATH}")
print(f"UI Path exists: {UI_PATH.exists()}")
if UI_PATH.exists():
    try:
        app.mount("/ui", StaticFiles(directory=str(UI_PATH), html=True), name="ui")
        print("[OK] UI static files mounted successfully")
    except Exception as e:
        print(f"[ERROR] Failed to mount UI: {e}")
else:
    print(f"[ERROR] UI path not found: {UI_PATH}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,  # Disabled for production
        log_level="info"
    )
