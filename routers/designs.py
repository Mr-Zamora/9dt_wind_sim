"""
Design management endpoints
Upload, retrieve, and delete vehicle designs
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import shutil
from datetime import datetime
import numpy as np

from models.schemas import DesignUploadResponse, ErrorResponse
from services.physics_service import PhysicsService

router = APIRouter()


def convert_numpy_types(obj):
    """Convert numpy types to Python native types"""
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

# Storage directory for uploaded STL files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=DesignUploadResponse)
async def upload_design(file: UploadFile = File(...)):
    """
    Upload STL file for analysis
    
    Args:
        file: STL file (binary or ASCII format)
        
    Returns:
        Design ID and basic file info
    """
    # Validate file extension
    if not file.filename.endswith('.stl'):
        raise HTTPException(
            status_code=400,
            detail="Only STL files are supported"
        )
    
    # Generate unique design ID
    design_id = str(uuid.uuid4())
    
    # Save file
    file_path = UPLOAD_DIR / f"{design_id}.stl"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Quick validation
    try:
        import traceback
        print(f"Analyzing STL file: {file_path}")
        analysis = PhysicsService.analyze_stl(str(file_path))
        print(f"Analysis complete. Keys: {analysis.keys()}")
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        return DesignUploadResponse(
            design_id=design_id,
            filename=file.filename,
            file_size_mb=round(file_size_mb, 2),
            num_triangles=analysis['stats']['num_triangles'],
            status="ready",
            message="File uploaded and validated successfully"
        )
    
    except Exception as e:
        # Clean up file on error
        import traceback
        print(f"Upload error: {e}")
        print(traceback.format_exc())
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid STL file: {str(e)}"
        )


@router.get("/{design_id}")
async def get_design(design_id: str):
    """
    Get design information
    
    Args:
        design_id: Unique design identifier
        
    Returns:
        Design metadata and geometry
    """
    file_path = UPLOAD_DIR / f"{design_id}.stl"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Design not found: {design_id}"
        )
    
    try:
        analysis = PhysicsService.analyze_stl(str(file_path))
        
        # Convert and flatten geometry for easier access
        geom = convert_numpy_types(analysis['geometry'])
        validation = convert_numpy_types(analysis['validation'])
        stats = convert_numpy_types(analysis['stats'])
        drag = convert_numpy_types(analysis['drag_analysis'])
        
        return {
            "design_id": design_id,
            "geometry": {
                "length_m": float(geom['dimensions']['length']),
                "width_m": float(geom['dimensions']['width']),
                "height_m": float(geom['dimensions']['height']),
                "frontal_area_m2": float(geom['frontal_area_m2']),
                "volume_m3": float(geom['volume_m3']),
                "volume_confidence": float(geom['volume_confidence']),
                "surface_area_m2": float(geom['surface_area_m2'])
            },
            "validation": validation,
            "stats": stats,
            "drag_estimate": {
                "cd": float(drag['estimated_cd']),
                "features": drag['features']
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze design: {str(e)}"
        )


@router.get("/{design_id}/stl")
async def get_design_stl(design_id: str):
    """
    Get raw STL file binary
    
    Args:
        design_id: Unique design identifier
        
    Returns:
        Raw STL file response
    """
    file_path = UPLOAD_DIR / f"{design_id}.stl"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Design STL not found: {design_id}"
        )
    
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=f"{design_id}.stl"
    )


@router.delete("/{design_id}")
async def delete_design(design_id: str):
    """
    Delete a design
    
    Args:
        design_id: Unique design identifier
        
    Returns:
        Deletion confirmation
    """
    file_path = UPLOAD_DIR / f"{design_id}.stl"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Design not found: {design_id}"
        )
    
    try:
        file_path.unlink()
        return {
            "design_id": design_id,
            "status": "deleted",
            "message": "Design deleted successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete design: {str(e)}"
        )
