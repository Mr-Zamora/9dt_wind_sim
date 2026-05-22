"""
Simulation endpoints
Run aerodynamic simulations and retrieve results
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from datetime import datetime
import uuid
import numpy as np

from models.schemas import (
    SimulationRequest,
    SimulationResult,
    MaterialComparisonResponse
)
from services.physics_service import PhysicsService

router = APIRouter()

UPLOAD_DIR = Path("uploads")


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


@router.post("/run", response_model=SimulationResult)
async def run_simulation(request: SimulationRequest):
    """
    Run aerodynamic simulation on uploaded design
    
    Args:
        request: Simulation parameters
        
    Returns:
        Complete simulation results
    """
    # Check if design exists
    file_path = UPLOAD_DIR / f"{request.design_id}.stl"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Design not found: {request.design_id}"
        )
    
    try:
        # Analyze STL
        analysis = PhysicsService.analyze_stl(str(file_path))
        
        # Run simulation
        sim_results = PhysicsService.run_simulation(
            mesh_data=analysis['mesh_data'],
            geometry=analysis['geometry'],
            drag_analysis=analysis['drag_analysis'],
            wind_speed_kmh=request.wind_speed_kmh,
            material=request.material.value,
            engine_power_hp=request.engine_power_hp,
            scale_mode=request.scale_mode.value,
            custom_mass_kg=request.custom_mass_kg
        )
        
        # Build response - convert all numpy types
        summary = convert_numpy_types(sim_results['summary'])
        wind_analysis = convert_numpy_types(sim_results['wind_speed_analysis'])
        geom = convert_numpy_types(analysis['geometry'])
        validation = convert_numpy_types(analysis['validation'])
        drag = convert_numpy_types(analysis['drag_analysis'])
        
        orig_length = float(geom['dimensions']['length'])
        scaled_length = float(summary['vehicle_specs']['length_m'])
        scale_factor = scaled_length / max(orig_length, 0.001)
        
        return SimulationResult(
            simulation_id=str(uuid.uuid4()),
            design_id=request.design_id,
            status="completed",
            
            # Geometry
            geometry={
                "length_m": float(geom['dimensions']['length']) * scale_factor,
                "width_m": float(geom['dimensions']['width']) * scale_factor,
                "height_m": float(geom['dimensions']['height']) * scale_factor,
                "frontal_area_m2": float(geom['frontal_area_m2']) * (scale_factor ** 2),
                "volume_m3": float(geom['volume_m3']) * (scale_factor ** 3),
                "volume_confidence": float(geom['volume_confidence']),
                "surface_area_m2": float(geom['surface_area_m2']) * (scale_factor ** 2)
            },
            
            # Validation
            validation={
                "is_valid": bool(validation['is_valid']),
                "quality_score": float(validation['quality_score']),
                "num_triangles": int(validation['num_triangles']),
                "issues": validation['issues'],
                "warnings": validation['warnings']
            },
            
            # Aerodynamics
            estimated_cd=float(drag['estimated_cd']),
            cd_corrected=float(wind_analysis['cd_corrected']),
            reynolds_number=float(wind_analysis['reynolds_number']),
            drag_force_n=float(wind_analysis['drag_force_n']),
            
            # Performance
            vehicle_mass_kg=float(summary['vehicle_specs']['mass_kg']),
            top_speed_kmh=float(summary['top_speed']['speed_kmh']),
            acceleration_0_100_sec=float(summary['acceleration']['0_100_kmh_sec']) if summary['acceleration']['0_100_kmh_sec'] else None,
            acceleration_0_60_sec=float(summary['acceleration']['0_60_kmh_sec']) if summary['acceleration']['0_60_kmh_sec'] else None,
            
            # Power breakdown
            aero_power_pct=float(summary['efficiency']['aero_power_pct']),
            rolling_power_pct=float(summary['efficiency']['rolling_power_pct']),
            
            # Metadata
            simulation_time_seconds=float(sim_results['simulation_time']),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {str(e)}"
        )


@router.get("/{design_id}/materials", response_model=MaterialComparisonResponse)
async def compare_materials(
    design_id: str,
    engine_power_hp: float = 150.0,
    scale_mode: str = "full_scale"
):
    """
    Compare performance across different materials
    
    Args:
        design_id: Unique design identifier
        engine_power_hp: Engine power in HP
        scale_mode: 'miniature' or 'full_scale'
        
    Returns:
        Material comparison results
    """
    file_path = UPLOAD_DIR / f"{design_id}.stl"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Design not found: {design_id}"
        )
    
    try:
        # Analyze STL
        analysis = PhysicsService.analyze_stl(str(file_path))
        
        # Compare materials
        comparison = PhysicsService.compare_materials(
            geometry=analysis['geometry'],
            estimated_cd=analysis['drag_analysis']['estimated_cd'],
            engine_power_hp=engine_power_hp,
            scale_mode=scale_mode
        )
        
        return MaterialComparisonResponse(
            design_id=design_id,
            materials=comparison
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Material comparison failed: {str(e)}"
        )


@router.get("/{design_id}/scales")
async def compare_scales(
    design_id: str,
    engine_power_hp: float = 150.0,
    miniature_length: float = 0.25
):
    """
    Compare miniature vs full-scale performance
    
    Args:
        design_id: Unique design identifier
        engine_power_hp: Engine power in HP
        miniature_length: Miniature model length in meters
        
    Returns:
        Scale comparison results
    """
    file_path = UPLOAD_DIR / f"{design_id}.stl"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Design not found: {design_id}"
        )
    
    try:
        # Analyze STL
        analysis = PhysicsService.analyze_stl(str(file_path))
        
        # Compare scales
        comparison = PhysicsService.compare_scales(
            geometry=analysis['geometry'],
            estimated_cd=analysis['drag_analysis']['estimated_cd'],
            engine_power_hp=engine_power_hp,
            miniature_length=miniature_length
        )
        
        return {
            "design_id": design_id,
            "comparison": comparison
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scale comparison failed: {str(e)}"
        )
