"""
AeroClass Physics Engine
Educational aerodynamics simulation for STEM classrooms
"""

__version__ = "0.1.0"
__author__ = "AeroClass Development Team"

from .stl_parser import STLParser
from .geometry_analyzer import GeometryAnalyzer
from .drag_estimator import DragEstimator
from .performance_calc import PerformanceCalculator

__all__ = [
    'STLParser',
    'GeometryAnalyzer',
    'DragEstimator',
    'PerformanceCalculator'
]
