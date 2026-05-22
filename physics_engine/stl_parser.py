"""
STL File Parser and Validator
Handles loading and basic validation of STL files
"""

import numpy as np
from stl import mesh
from pathlib import Path
from typing import Tuple, Dict, Optional


class STLParser:
    """Parse and validate STL files for aerodynamic simulation"""
    
    MAX_FILE_SIZE_MB = 100
    MAX_TRIANGLES = 1_000_000
    
    def __init__(self, filepath: str):
        """
        Initialize STL parser
        
        Args:
            filepath: Path to STL file (binary or ASCII format)
        """
        self.filepath = Path(filepath)
        self.mesh_data: Optional[mesh.Mesh] = None
        self.validation_results: Dict = {}
        
    def load(self) -> mesh.Mesh:
        """
        Load STL file into memory
        
        Returns:
            mesh.Mesh object containing triangle data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large or invalid format
        """
        if not self.filepath.exists():
            raise FileNotFoundError(f"STL file not found: {self.filepath}")
        
        # Check file size
        file_size_mb = self.filepath.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File too large: {file_size_mb:.1f}MB "
                f"(max {self.MAX_FILE_SIZE_MB}MB)"
            )
        
        # Load mesh
        try:
            self.mesh_data = mesh.Mesh.from_file(str(self.filepath))
        except Exception as e:
            raise ValueError(f"Failed to parse STL file: {str(e)}")
        
        # Check triangle count
        num_triangles = len(self.mesh_data.vectors)
        if num_triangles > self.MAX_TRIANGLES:
            raise ValueError(
                f"Too many triangles: {num_triangles:,} "
                f"(max {self.MAX_TRIANGLES:,})"
            )
        
        return self.mesh_data
    
    def validate(self) -> Dict:
        """
        Validate mesh quality and detect common issues
        
        Returns:
            Dictionary containing validation results:
            {
                'is_valid': bool,
                'num_triangles': int,
                'issues': List[str],
                'warnings': List[str],
                'quality_score': float (0-100)
            }
        """
        if self.mesh_data is None:
            raise RuntimeError("Must call load() before validate()")
        
        issues = []
        warnings = []
        
        # Check for degenerate triangles (zero area)
        degenerate_count = self._check_degenerate_triangles()
        if degenerate_count > 0:
            issues.append(f"{degenerate_count} degenerate triangles (zero area)")
        
        # Check for inverted normals
        inverted_count = self._check_inverted_normals()
        if inverted_count > 0:
            warnings.append(f"{inverted_count} potentially inverted normals")
        
        # Check for duplicate vertices
        duplicate_count = self._check_duplicate_vertices()
        if duplicate_count > 10:
            warnings.append(f"{duplicate_count} duplicate vertices detected")
        
        # Calculate quality score
        num_triangles = len(self.mesh_data.vectors)
        quality_score = 100.0
        quality_score -= min(degenerate_count / num_triangles * 50, 50)
        quality_score -= min(inverted_count / num_triangles * 30, 30)
        quality_score -= min(duplicate_count / num_triangles * 20, 20)
        
        self.validation_results = {
            'is_valid': len(issues) == 0,
            'num_triangles': num_triangles,
            'issues': issues,
            'warnings': warnings,
            'quality_score': max(0, quality_score)
        }
        
        return self.validation_results
    
    def _check_degenerate_triangles(self) -> int:
        """Count triangles with zero or near-zero area"""
        count = 0
        for triangle in self.mesh_data.vectors:
            # Calculate triangle area using cross product
            v1 = triangle[1] - triangle[0]
            v2 = triangle[2] - triangle[0]
            area = 0.5 * np.linalg.norm(np.cross(v1, v2))
            
            if area < 1e-10:  # Essentially zero area
                count += 1
        
        return count
    
    def _check_inverted_normals(self) -> int:
        """
        Check for normals pointing inward (heuristic check)
        Assumes most normals should point outward from centroid
        """
        # Calculate mesh centroid
        all_vertices = self.mesh_data.vectors.reshape(-1, 3)
        centroid = np.mean(all_vertices, axis=0)
        
        inverted_count = 0
        for i, triangle in enumerate(self.mesh_data.vectors):
            # Triangle center
            tri_center = np.mean(triangle, axis=0)
            
            # Vector from centroid to triangle center
            outward_direction = tri_center - centroid
            
            # Compare with stored normal
            normal = self.mesh_data.normals[i]
            
            # If normal points opposite to outward direction, it might be inverted
            if np.dot(normal, outward_direction) < 0:
                inverted_count += 1
        
        return inverted_count
    
    def _check_duplicate_vertices(self) -> int:
        """Count duplicate vertices (within tolerance)"""
        all_vertices = self.mesh_data.vectors.reshape(-1, 3)
        unique_vertices = np.unique(
            np.round(all_vertices, decimals=6),
            axis=0
        )
        
        return len(all_vertices) - len(unique_vertices)
    
    def get_stats(self) -> Dict:
        """
        Get basic mesh statistics
        
        Returns:
            Dictionary with mesh statistics
        """
        if self.mesh_data is None:
            raise RuntimeError("Must call load() before get_stats()")
        
        all_vertices = self.mesh_data.vectors.reshape(-1, 3)
        
        return {
            'num_triangles': len(self.mesh_data.vectors),
            'num_vertices': len(all_vertices),
            'file_size_mb': self.filepath.stat().st_size / (1024 * 1024),
            'bounds': {
                'min': all_vertices.min(axis=0).tolist(),
                'max': all_vertices.max(axis=0).tolist()
            }
        }
