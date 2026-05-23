"""
ASGI entry point for PythonAnywhere deployment
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for production if not set
if not os.getenv("UPLOAD_DIR"):
    os.environ["UPLOAD_DIR"] = str(project_root / "uploads")
if not os.getenv("UI_PATH"):
    os.environ["UI_PATH"] = str(project_root / "UI_test")

from main import app  # noqa: F401 - app is used by PythonAnywhere ASGI server
