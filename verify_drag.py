"""
Quick smoke test for the new pressure-integration drag estimator.
Run from the project root:  python verify_drag.py
"""
import sys, os, glob
sys.path.insert(0, 'physics_engine')

from stl_parser import STLParser
from geometry_analyzer import GeometryAnalyzer
from drag_estimator import DragEstimator

# ── pick the most recently uploaded STL ──────────────────────────────────────
uploads = sorted(glob.glob('uploads/*.stl'), key=os.path.getmtime, reverse=True)
if not uploads:
    print("No STL files found in uploads/"); sys.exit(1)

stl_path = uploads[0]
print(f"STL: {os.path.basename(stl_path)}")

# ── parse & analyse ──────────────────────────────────────────────────────────
parser   = STLParser(stl_path)
mesh     = parser.load()

analyzer = GeometryAnalyzer(mesh)
props    = analyzer.get_all_properties()
d        = props['dimensions']
bb       = props['bounding_box']

print(f"\n-- Geometry (fixed axis assignment) ----------------------------------")
print(f"  Length (nose-to-tail) : {d['length']*1000:7.1f} mm  [raw axis {bb['length_axis']}]")
print(f"  Width  (side-to-side) : {d['width'] *1000:7.1f} mm  [raw axis {bb['width_axis']}]")
print(f"  Height (floor-to-roof): {d['height']*1000:7.1f} mm  [raw axis {bb['height_axis']}]")
print(f"  Frontal area          : {props['frontal_area_m2']*10000:7.2f} cm²")
print(f"  Volume                : {props['volume_m3']*1e6:7.2f} cm³")

# ── drag estimator ───────────────────────────────────────────────────────────
estimator = DragEstimator(mesh, props['frontal_area_m2'])
analysis  = estimator.get_detailed_analysis()
cd        = analysis['estimated_cd']
factors   = analysis['factors']
features  = analysis['features']
breakdown = analysis['drag_breakdown']

print(f"\n── Drag (pressure integration) ───────────────────────────────────")
print(f"  Cd (total)     : {cd:.4f}")
print(f"  Pressure Cd    : {factors['pressure_cd']:.4f}")
print(f"  Wake Cd        : {factors['wake_cd']:.4f}")
print(f"  Friction Cd    : {factors['friction_cd']:.4f}")
print(f"  Flow direction : {factors['flow_direction']}")
print(f"\n── Breakdown (%) ─────────────────────────────────────────────────")
print(f"  Pressure drag  : {breakdown['pressure_drag_pct']:.1f}%")
print(f"  Skin friction  : {breakdown['skin_friction_pct']:.1f}%")
print(f"  Wake drag      : {breakdown['wake_drag_pct']:.1f}%")
print(f"\n── Shape features ────────────────────────────────────────────────")
print(f"  Fineness ratio : {features['fineness_ratio']:.2f}")
print(f"  Nose radius    : {features['nose_radius']*1000:.1f} mm")
print(f"  Rear taper     : {features['rear_taper_angle']:.1f}°")
print(f"  Smoothness     : {features['surface_smoothness']:.3f}")
print(f"  Underbody flat : {features['underbody_flatness']:.3f}")

print(f"\n── Sanity ────────────────────────────────────────────────────────")
print(f"  Expected Cd range for foam classroom car: 0.35 – 0.60")
ok = 0.20 < cd < 0.80
print(f"  {'PASS ✓' if ok else 'FAIL ✗ — check calibration'}")
