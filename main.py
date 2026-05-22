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

# Create FastAPI app
app = FastAPI(
    title="AeroClass API",
    description="Educational aerodynamics simulation API for STEM classrooms",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify frontend domain
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
UI_PATH = Path(__file__).parent / "UI_test"
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
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
