"""
Application configuration using environment variables
"""
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "AeroClass API"
    api_version: str = "0.1.0"

    # CORS Configuration
    cors_origins: str = "*"  # Comma-separated list for production

    # File Storage
    upload_dir: str = "uploads"
    max_file_size_mb: int = 100
    max_triangles: int = 1_000_000

    # UI Configuration
    ui_path: str = "UI_test"

    # Physics Engine
    physics_engine_path: str = "physics_engine"

    # PythonAnywhere specific
    is_pythonanywhere: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origins_list(self) -> list:
        """Convert comma-separated string to list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def upload_path(self) -> Path:
        """Get upload directory as Path object and ensure it exists"""
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def ui_path_obj(self) -> Path:
        """Get UI directory as Path object"""
        return Path(self.ui_path)


settings = Settings()
