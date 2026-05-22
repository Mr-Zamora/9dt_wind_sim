"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from enum import Enum


class SimulationMode(str, Enum):
    """Simulation mode options"""
    QUICK_PREVIEW = "quick_preview"
    DETAILED_ANALYSIS = "detailed_analysis"


class ScaleMode(str, Enum):
    """Scale mode options"""
    MINIATURE = "miniature"
    FULL_SCALE = "full_scale"


class Material(str, Enum):
    """Available materials"""
    CARBON_FIBER = "carbon_fiber"
    ALUMINUM = "aluminum"
    STEEL = "steel"
    ABS_PLASTIC = "abs_plastic"
    BALSA_WOOD = "balsa_wood"


# Request models
class SimulationRequest(BaseModel):
    """Request to run aerodynamic simulation"""
    design_id: str = Field(..., description="Unique design identifier")
    simulation_mode: SimulationMode = Field(
        SimulationMode.QUICK_PREVIEW,
        description="Simulation complexity level"
    )
    wind_speed_kmh: float = Field(
        100.0,
        ge=0,
        le=150,
        description="Wind speed in km/h"
    )
    moving_floor: bool = Field(
        True,
        description="Enable moving ground plane"
    )
    scale_mode: ScaleMode = Field(
        ScaleMode.FULL_SCALE,
        description="Miniature or full-scale analysis"
    )
    material: Material = Field(
        Material.ALUMINUM,
        description="Vehicle material"
    )
    engine_power_hp: float = Field(
        150.0,
        ge=10,
        le=1000,
        description="Engine power in horsepower"
    )


class GeometryData(BaseModel):
    """Geometric properties of uploaded design"""
    length_m: float
    width_m: float
    height_m: float
    frontal_area_m2: float
    volume_m3: float
    volume_confidence: float
    surface_area_m2: float


class ValidationResult(BaseModel):
    """Mesh validation results"""
    is_valid: bool
    quality_score: float
    num_triangles: int
    issues: List[str] = []
    warnings: List[str] = []


# Response models
class SimulationResult(BaseModel):
    """Complete simulation results"""
    simulation_id: str
    design_id: str
    status: str
    
    # Geometry
    geometry: GeometryData
    validation: ValidationResult
    
    # Aerodynamics
    estimated_cd: float
    cd_corrected: float
    reynolds_number: float
    drag_force_n: float
    
    # Performance
    vehicle_mass_kg: float
    top_speed_kmh: float
    acceleration_0_100_sec: Optional[float]
    acceleration_0_60_sec: Optional[float]
    
    # Power breakdown
    aero_power_pct: float
    rolling_power_pct: float
    
    # Metadata
    simulation_time_seconds: float
    timestamp: str


class DesignUploadResponse(BaseModel):
    """Response after STL upload"""
    design_id: str
    filename: str
    file_size_mb: float
    num_triangles: int
    status: str
    message: str


class MaterialComparisonResponse(BaseModel):
    """Material comparison results"""
    design_id: str
    materials: Dict[str, Dict]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    physics_engine: str
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    timestamp: str
