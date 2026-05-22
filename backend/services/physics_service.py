"""
Physics Service
Wrapper for physics engine modules
"""

import sys
from pathlib import Path
import time
from typing import Dict, Tuple

# Add physics engine to path
PHYSICS_ENGINE_PATH = Path(__file__).parent.parent.parent / "physics_engine"
sys.path.insert(0, str(PHYSICS_ENGINE_PATH))

from stl_parser import STLParser
from geometry_analyzer import GeometryAnalyzer
from drag_estimator import DragEstimator
from performance_calc import PerformanceCalculator


class PhysicsService:
    """Service layer for physics calculations"""
    
    @staticmethod
    def analyze_stl(filepath: str) -> Dict:
        """
        Complete STL analysis pipeline
        
        Args:
            filepath: Path to STL file
            
        Returns:
            Dictionary with all analysis results
        """
        start_time = time.time()
        
        # Parse and validate
        parser = STLParser(filepath)
        mesh_data = parser.load()
        validation = parser.validate()
        stats = parser.get_stats()
        
        # Analyze geometry
        analyzer = GeometryAnalyzer(mesh_data)
        geometry = analyzer.get_all_properties()
        
        # Estimate drag
        drag_estimator = DragEstimator(mesh_data, geometry['frontal_area_m2'])
        drag_analysis = drag_estimator.get_detailed_analysis()
        
        elapsed_time = time.time() - start_time
        
        return {
            'mesh_data': mesh_data,
            'validation': validation,
            'stats': stats,
            'geometry': geometry,
            'drag_analysis': drag_analysis,
            'processing_time': elapsed_time
        }
    
    @staticmethod
    def run_simulation(
        mesh_data,
        geometry: Dict,
        drag_analysis: Dict,
        wind_speed_kmh: float = 100.0,
        material: str = 'aluminum',
        engine_power_hp: float = 150.0,
        scale_mode: str = 'full_scale'
    ) -> Dict:
        """
        Run performance simulation
        
        Args:
            mesh_data: STL mesh object
            geometry: Geometric properties
            drag_analysis: Drag estimation results
            wind_speed_kmh: Wind speed in km/h
            material: Material name
            engine_power_hp: Engine power in HP
            scale_mode: 'miniature' or 'full_scale'
            
        Returns:
            Complete simulation results
        """
        start_time = time.time()
        
        # Create performance calculator
        perf_calc = PerformanceCalculator(
            cd=drag_analysis['estimated_cd'],
            frontal_area=geometry['frontal_area_m2'],
            volume=geometry['volume_m3'],
            material=material
        )
        
        # Get complete performance summary
        summary = perf_calc.get_performance_summary(
            power_hp=engine_power_hp,
            length=geometry['dimensions']['length'],
            scale_mode=scale_mode
        )
        
        # Calculate drag at specified wind speed
        wind_speed_ms = wind_speed_kmh / 3.6
        cd_at_speed, reynolds = perf_calc.apply_reynolds_correction(
            wind_speed_ms,
            geometry['dimensions']['length'],
            scale_mode
        )
        
        drag_force = 0.5 * 1.225 * (wind_speed_ms ** 2) * cd_at_speed * geometry['frontal_area_m2']
        
        elapsed_time = time.time() - start_time
        
        return {
            'summary': summary,
            'wind_speed_analysis': {
                'wind_speed_kmh': wind_speed_kmh,
                'wind_speed_ms': wind_speed_ms,
                'reynolds_number': reynolds,
                'cd_corrected': cd_at_speed,
                'drag_force_n': drag_force
            },
            'drag_features': drag_analysis['features'],
            'simulation_time': elapsed_time
        }
    
    @staticmethod
    def compare_materials(
        geometry: Dict,
        estimated_cd: float,
        engine_power_hp: float = 150.0,
        scale_mode: str = 'full_scale'
    ) -> Dict:
        """
        Compare performance across all materials
        
        Args:
            geometry: Geometric properties
            estimated_cd: Drag coefficient
            engine_power_hp: Engine power in HP
            scale_mode: 'miniature' or 'full_scale'
            
        Returns:
            Material comparison results
        """
        perf_calc = PerformanceCalculator(
            cd=estimated_cd,
            frontal_area=geometry['frontal_area_m2'],
            volume=geometry['volume_m3'],
            material='aluminum'  # Temporary, will iterate
        )
        
        comparison = perf_calc.compare_materials(
            power_watts=engine_power_hp * 745.7,
            length=geometry['dimensions']['length'],
            scale_mode=scale_mode
        )
        
        return comparison
    
    @staticmethod
    def compare_scales(
        geometry: Dict,
        estimated_cd: float,
        engine_power_hp: float = 150.0,
        miniature_length: float = 0.25
    ) -> Dict:
        """
        Compare miniature vs full-scale performance
        
        Args:
            geometry: Geometric properties
            estimated_cd: Drag coefficient
            engine_power_hp: Engine power in HP
            miniature_length: Miniature model length in meters
            
        Returns:
            Scale comparison results
        """
        perf_calc = PerformanceCalculator(
            cd=estimated_cd,
            frontal_area=geometry['frontal_area_m2'],
            volume=geometry['volume_m3'],
            material='aluminum'
        )
        
        comparison = perf_calc.scale_comparison(
            power_watts=engine_power_hp * 745.7,
            miniature_length=miniature_length,
            full_scale_length=geometry['dimensions']['length']
        )
        
        return comparison
