import sys, os, glob
sys.path.insert(0, 'physics_engine')

from geometry_analyzer import GeometryAnalyzer
from stl_parser import STLParser

uploads = sorted(glob.glob('uploads/*.stl'), key=os.path.getmtime, reverse=True)
stl_path = uploads[0]
print(f'Testing: {stl_path}')

parser = STLParser(stl_path)
mesh = parser.load()

analyzer = GeometryAnalyzer(mesh)
props = analyzer.get_all_properties()
d = props['dimensions']
bb = props['bounding_box']

length_mm = d['length'] * 1000
width_mm  = d['width']  * 1000
height_mm = d['height'] * 1000
area_cm2  = props['frontal_area_m2'] * 10000
vol_cm3   = props['volume_m3'] * 1e6

print(f"Length (nose-to-tail): {length_mm:.1f} mm  [raw axis {bb['length_axis']}]")
print(f"Width  (side-to-side): {width_mm:.1f} mm  [raw axis {bb['width_axis']}]")
print(f"Height (floor-to-roof): {height_mm:.1f} mm  [raw axis {bb['height_axis']}]")
print(f"Frontal area: {area_cm2:.2f} cm2")
print(f"Volume: {vol_cm3:.2f} cm3")
print()
print("--- Sanity check for miniature mode (no scaling) ---")
print(f"Expected from badge: L=177.8mm  W=61.3mm  H=42.1mm")
print(f"Got:                 L={length_mm:.1f}mm  W={width_mm:.1f}mm  H={height_mm:.1f}mm")
