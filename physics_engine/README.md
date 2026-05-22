# AeroClass Physics Engine

Educational aerodynamics simulation engine for STEM classrooms.

## Overview

This Python package provides simplified aerodynamic calculations optimized for educational accuracy (15-25% error tolerance). It's designed to run quickly (<60 seconds) while teaching core aerodynamic principles.

## Modules

### 1. `stl_parser.py`
- Load and validate STL files (binary/ASCII)
- Check for mesh defects (degenerate triangles, inverted normals)
- Calculate quality scores

### 2. `geometry_analyzer.py`
- Calculate frontal area using ray-casting projection
- Estimate volume using voxel-based method (robust to defects)
- Compute bounding box and surface area

### 3. `drag_estimator.py`
- Quick Preview mode: Empirical Cd estimation
- Feature-based analysis (nose radius, rear taper, smoothness)
- Drag force calculations

### 4. `performance_calc.py`
- Top speed prediction (power balance method)
- 0-100 km/h acceleration simulation
- Reynolds number corrections for dual-scale system
- Material comparison analysis

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Without STL File (Synthetic Demo)
```bash
python demo.py
```

### With STL File
```bash
python demo.py path/to/your/vehicle.stl
```

## Usage Example

```python
from stl_parser import STLParser
from geometry_analyzer import GeometryAnalyzer
from drag_estimator import DragEstimator
from performance_calc import PerformanceCalculator

# Load STL
parser = STLParser("vehicle.stl")
mesh = parser.load()
validation = parser.validate()

# Analyze geometry
analyzer = GeometryAnalyzer(mesh)
props = analyzer.get_all_properties()

# Estimate drag
drag_est = DragEstimator(mesh, props['frontal_area_m2'])
analysis = drag_est.get_detailed_analysis()
cd = analysis['estimated_cd']

# Calculate performance
perf = PerformanceCalculator(
    cd=cd,
    frontal_area=props['frontal_area_m2'],
    volume=props['volume_m3'],
    material='aluminum'
)

summary = perf.get_performance_summary(power_hp=150)
print(f"Top Speed: {summary['top_speed']['speed_kmh']:.1f} km/h")
print(f"0-100 km/h: {summary['acceleration']['0_100_kmh_sec']:.2f} sec")
```

## Accuracy & Limitations

- **Target Accuracy**: 15-25% error vs professional CFD
- **Best For**: Comparative analysis, design iteration learning
- **Not For**: Final engineering validation, production vehicles

### Known Limitations
1. Simplified pressure field (no full Navier-Stokes)
2. No lift/downforce calculations
3. No wheel rotation effects
4. Simplified boundary layer modeling

## Materials Supported

- Carbon Fiber (1,750 kg/m³)
- Aluminum 6061-T6 (2,700 kg/m³)
- Mild Steel (7,850 kg/m³)
- ABS Plastic (1,040 kg/m³)
- Balsa Wood (130 kg/m³)

## Reynolds Number Corrections

### Miniature Scale (<1m)
- Re < 10⁵: +25% Cd penalty
- Re < 5×10⁵: +15% Cd penalty
- Re < 10⁶: +5% Cd penalty

### Full Scale (>3m)
- Re > 10⁶: -8% Cd reduction

## Testing

```bash
pytest tests/ -v --cov=physics_engine
```

## Next Steps

1. ✅ Core physics engine complete
2. 🚧 Unit tests (in progress)
3. 📋 FastAPI backend wrapper
4. 📋 WebAssembly compilation for browser
5. 📋 GPU-accelerated panel method solver

## License

Educational use - AeroClass Project

## Authors

AeroClass Development Team
