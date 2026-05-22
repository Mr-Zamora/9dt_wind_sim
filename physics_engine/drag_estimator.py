"""
Drag Coefficient Estimator
Quick preview mode using empirical methods and geometric feature analysis
"""

import numpy as np
from typing import Dict
from stl import mesh


class DragEstimator:
    """Estimate drag coefficient using simplified empirical methods"""
    
    # Air density at sea level, 15°C
    RHO_AIR = 1.225  # kg/m³
    
    # Base drag coefficients for common shapes
    BASE_CD_DATABASE = {
        'streamlined': 0.25,
        'sedan': 0.30,
        'suv': 0.35,
        'box': 0.45,
        'sphere': 0.47
    }
    
    def __init__(self, mesh_data: mesh.Mesh, frontal_area: float):
        """
        Initialize drag estimator
        
        Args:
            mesh_data: numpy-stl Mesh object
            frontal_area: Frontal area in m²
        """
        self.mesh = mesh_data
        self.frontal_area = frontal_area
        self.features: Dict = {}
        
    def analyze_features(self) -> Dict:
        """
        Analyze geometric features that affect drag
        
        Returns:
            Dictionary of feature measurements
        """
        vertices = self.mesh.vectors.reshape(-1, 3)
        
        # Get bounding box
        min_coords = vertices.min(axis=0)
        max_coords = vertices.max(axis=0)
        dimensions = max_coords - min_coords
        
        length = dimensions[0]  # Assuming X is flow direction
        width = dimensions[1]
        height = dimensions[2]
        
        self.features = {
            'length': length,
            'width': width,
            'height': height,
            'aspect_ratio': length / max(width, 0.001),
            'fineness_ratio': length / max(np.sqrt(width * height), 0.001),
            'nose_radius': self._estimate_nose_radius(vertices, min_coords[0], length),
            'rear_taper_angle': self._estimate_rear_taper(vertices, max_coords[0], length),
            'surface_smoothness': self._estimate_surface_smoothness(),
            'underbody_flatness': self._estimate_underbody_flatness(vertices, height)
        }
        
        return self.features
    
    def estimate_cd_quick(self) -> float:
        """
        Quick drag coefficient estimation using geometric features
        
        Returns:
            Estimated drag coefficient (Cd)
        """
        if not self.features:
            self.analyze_features()
        
        # Start with base Cd based on overall shape
        base_cd = self._get_base_cd()
        
        # Apply corrections based on features
        cd = base_cd
        
        # Nose shape correction
        nose_factor = self._nose_correction_factor()
        cd *= nose_factor
        
        # Rear taper correction
        rear_factor = self._rear_correction_factor()
        cd *= rear_factor
        
        # Surface smoothness correction
        smoothness_factor = self._smoothness_correction_factor()
        cd *= smoothness_factor
        
        # Underbody correction
        underbody_factor = self._underbody_correction_factor()
        cd *= underbody_factor
        
        # Aspect ratio correction
        aspect_factor = self._aspect_ratio_correction()
        cd *= aspect_factor
        
        return cd
    
    def calculate_drag_force(self, velocity: float, cd: float = None) -> float:
        """
        Calculate drag force at given velocity
        
        Args:
            velocity: Air velocity in m/s
            cd: Drag coefficient (if None, will estimate)
            
        Returns:
            Drag force in Newtons
        """
        if cd is None:
            cd = self.estimate_cd_quick()
        
        # F_d = 0.5 * ρ * v² * Cd * A
        drag_force = 0.5 * self.RHO_AIR * (velocity ** 2) * cd * self.frontal_area
        
        return drag_force
    
    def _get_base_cd(self) -> float:
        """Determine base Cd from overall shape classification"""
        fineness = self.features['fineness_ratio']
        
        if fineness > 4.0:
            return self.BASE_CD_DATABASE['streamlined']
        elif fineness > 3.0:
            return self.BASE_CD_DATABASE['sedan']
        elif fineness > 2.0:
            return self.BASE_CD_DATABASE['suv']
        else:
            return self.BASE_CD_DATABASE['box']
    
    def _estimate_nose_radius(self, vertices: np.ndarray, front_x: float, length: float) -> float:
        """
        Estimate leading edge radius (nose bluntness)
        
        Args:
            vertices: All mesh vertices
            front_x: X-coordinate of front face
            length: Vehicle length
            
        Returns:
            Estimated nose radius in meters
        """
        # Get vertices near front (within 10% of length)
        threshold = front_x + length * 0.1
        front_vertices = vertices[vertices[:, 0] < threshold]
        
        if len(front_vertices) < 3:
            return 0.1  # Default moderate radius
        
        # Estimate curvature from vertex distribution
        y_range = front_vertices[:, 1].max() - front_vertices[:, 1].min()
        z_range = front_vertices[:, 2].max() - front_vertices[:, 2].min()
        
        # Rough radius estimate
        radius = (y_range + z_range) / 4.0
        
        return max(0.01, min(radius, 0.5))  # Clamp to reasonable range
    
    def _estimate_rear_taper(self, vertices: np.ndarray, rear_x: float, length: float) -> float:
        """
        Estimate rear taper angle (boat-tailing)
        
        Args:
            vertices: All mesh vertices
            rear_x: X-coordinate of rear face
            length: Vehicle length
            
        Returns:
            Taper angle in degrees (0 = vertical, positive = tapered)
        """
        # Get vertices in rear 30% of length
        threshold = rear_x - length * 0.3
        rear_vertices = vertices[vertices[:, 0] > threshold]
        
        if len(rear_vertices) < 10:
            return 0.0  # Vertical rear
        
        # Analyze how cross-section changes
        # Divide rear section into slices
        x_slices = np.linspace(threshold, rear_x, 5)
        areas = []
        
        for x in x_slices:
            slice_verts = rear_vertices[np.abs(rear_vertices[:, 0] - x) < 0.05]
            if len(slice_verts) > 0:
                y_range = slice_verts[:, 1].max() - slice_verts[:, 1].min()
                z_range = slice_verts[:, 2].max() - slice_verts[:, 2].min()
                areas.append(y_range * z_range)
        
        if len(areas) < 2:
            return 0.0
        
        # Calculate taper angle from area reduction
        area_ratio = areas[-1] / max(areas[0], 0.001)
        
        if area_ratio < 0.7:
            return 15.0  # Good taper
        elif area_ratio < 0.9:
            return 5.0   # Slight taper
        else:
            return 0.0   # Vertical/blunt rear
    
    def _estimate_surface_smoothness(self) -> float:
        """
        Estimate surface smoothness from triangle size variation
        
        Returns:
            Smoothness score (0-1, higher is smoother)
        """
        areas = []
        for triangle in self.mesh.vectors:
            v1 = triangle[1] - triangle[0]
            v2 = triangle[2] - triangle[0]
            area = 0.5 * np.linalg.norm(np.cross(v1, v2))
            areas.append(area)
        
        if len(areas) == 0:
            return 0.5
        
        # Calculate coefficient of variation
        mean_area = np.mean(areas)
        std_area = np.std(areas)
        
        if mean_area < 1e-10:
            return 0.5
        
        cv = std_area / mean_area
        
        # Lower CV = more uniform triangles = smoother surface
        smoothness = 1.0 / (1.0 + cv)
        
        return smoothness
    
    def _estimate_underbody_flatness(self, vertices: np.ndarray, height: float) -> float:
        """
        Estimate how flat the underbody is
        
        Args:
            vertices: All mesh vertices
            height: Vehicle height
            
        Returns:
            Flatness score (0-1, higher is flatter)
        """
        # Get bottom 20% of vertices
        z_threshold = vertices[:, 2].min() + height * 0.2
        bottom_verts = vertices[vertices[:, 2] < z_threshold]
        
        if len(bottom_verts) < 10:
            return 0.5
        
        # Calculate Z-coordinate variation
        z_std = np.std(bottom_verts[:, 2])
        
        # Normalize: low variation = flat
        flatness = 1.0 - min(z_std / (height * 0.1), 1.0)
        
        return flatness
    
    def _nose_correction_factor(self) -> float:
        """Correction factor based on nose radius"""
        radius = self.features['nose_radius']
        
        # Sharp nose (small radius) = lower drag
        # Blunt nose (large radius) = higher drag
        if radius < 0.05:
            return 0.95  # Sharp, good
        elif radius < 0.15:
            return 1.0   # Moderate
        else:
            return 1.1   # Blunt, bad
    
    def _rear_correction_factor(self) -> float:
        """Correction factor based on rear taper"""
        taper = self.features['rear_taper_angle']
        
        # Good taper reduces drag
        if taper > 10:
            return 0.90  # Excellent taper
        elif taper > 3:
            return 0.95  # Good taper
        else:
            return 1.05  # Blunt rear (high drag)
    
    def _smoothness_correction_factor(self) -> float:
        """Correction factor based on surface smoothness"""
        smoothness = self.features['surface_smoothness']
        
        # Smoother surface = lower drag
        return 0.95 + (1.0 - smoothness) * 0.1
    
    def _underbody_correction_factor(self) -> float:
        """Correction factor based on underbody flatness"""
        flatness = self.features['underbody_flatness']
        
        # Flat underbody reduces drag
        return 0.97 + (1.0 - flatness) * 0.08
    
    def _aspect_ratio_correction(self) -> float:
        """Correction factor based on aspect ratio"""
        aspect = self.features['aspect_ratio']
        
        # Very wide or very narrow vehicles have higher drag
        if 2.0 < aspect < 3.5:
            return 1.0   # Optimal
        elif 1.5 < aspect < 4.5:
            return 1.05  # Acceptable
        else:
            return 1.15  # Poor aspect ratio
    
    def get_detailed_analysis(self) -> Dict:
        """
        Get detailed drag analysis with all factors
        
        Returns:
            Dictionary with Cd estimate and all correction factors
        """
        if not self.features:
            self.analyze_features()
        
        base_cd = self._get_base_cd()
        
        factors = {
            'base_cd': base_cd,
            'nose_factor': self._nose_correction_factor(),
            'rear_factor': self._rear_correction_factor(),
            'smoothness_factor': self._smoothness_correction_factor(),
            'underbody_factor': self._underbody_correction_factor(),
            'aspect_factor': self._aspect_ratio_correction()
        }
        
        final_cd = base_cd
        for key, value in factors.items():
            if key != 'base_cd':
                final_cd *= value
        
        return {
            'estimated_cd': final_cd,
            'factors': factors,
            'features': self.features,
            'drag_breakdown': {
                'pressure_drag_pct': 75.0,  # Typical for vehicles
                'skin_friction_pct': 15.0,
                'induced_drag_pct': 10.0
            }
        }
