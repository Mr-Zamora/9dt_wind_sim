"""
AeroClass Physics Engine Demo
Demonstrates all calculation modules with sample data
"""

import json
from pathlib import Path


def demo_without_stl():
    """
    Demo using synthetic data (no STL file required)
    Simulates a typical sedan-like vehicle
    """
    print("=" * 70)
    print("AEROCLASS PHYSICS ENGINE DEMO")
    print("=" * 70)
    print()
    
    # Synthetic vehicle data (typical sedan)
    print("[GEOMETRY] Vehicle Geometry (Synthetic Data)")
    print("-" * 70)
    
    geometry = {
        'dimensions': {
            'length': 4.52,
            'width': 1.83,
            'height': 1.41
        },
        'frontal_area_m2': 2.14,
        'volume_m3': 3.87,
        'surface_area_m2': 28.3
    }
    
    for key, value in geometry.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for k, v in value.items():
                print(f"  {k}: {v:.2f} m" if 'length' in k or 'width' in k or 'height' in k else f"  {k}: {v:.2f}")
        else:
            print(f"{key}: {value:.2f}")
    
    print()
    
    # Import modules
    from drag_estimator import DragEstimator
    from performance_calc import PerformanceCalculator
    
    print("[DRAG] Drag Coefficient Estimation")
    print("-" * 70)
    
    # Simulate drag estimation (without actual mesh)
    estimated_cd = 0.29  # Typical sedan value
    print(f"Estimated Cd: {estimated_cd:.3f}")
    print(f"Classification: Good (sedan-like aerodynamics)")
    print()
    
    print("Feature Analysis:")
    features = {
        'fineness_ratio': 3.2,
        'nose_radius': 0.12,
        'rear_taper_angle': 5.0,
        'surface_smoothness': 0.85,
        'underbody_flatness': 0.75
    }
    
    for feature, value in features.items():
        print(f"  {feature}: {value:.2f}")
    
    print()
    
    # Performance calculations
    print("[PERFORMANCE] Performance Analysis")
    print("-" * 70)
    
    # Test with aluminum material
    perf_calc = PerformanceCalculator(
        cd=estimated_cd,
        frontal_area=geometry['frontal_area_m2'],
        volume=geometry['volume_m3'],
        material='aluminum'
    )
    
    print(f"Material: Aluminum")
    print(f"Mass: {perf_calc.mass:.0f} kg")
    print()
    
    # Top speed calculation
    power_hp = 150
    power_watts = power_hp * 745.7
    
    print(f"Engine Power: {power_hp} HP ({power_watts/1000:.1f} kW)")
    print()
    
    top_speed_data = perf_calc.calculate_top_speed(
        power_watts=power_watts,
        length=geometry['dimensions']['length'],
        scale_mode='full_scale'
    )
    
    print("Top Speed Analysis:")
    print(f"  Predicted Top Speed: {top_speed_data['top_speed_kmh']:.1f} km/h ({top_speed_data['top_speed_ms']:.1f} m/s)")
    print(f"  Reynolds Number: {top_speed_data['reynolds_number']:.2e}")
    print(f"  Cd (Reynolds corrected): {top_speed_data['cd_corrected']:.3f}")
    print(f"  Drag Force @ Top Speed: {top_speed_data['drag_force_n']:.0f} N")
    print()
    
    print("Power Breakdown at Top Speed:")
    print(f"  Aerodynamic Drag: {top_speed_data['power_breakdown']['aerodynamic_pct']:.1f}%")
    print(f"  Rolling Resistance: {top_speed_data['power_breakdown']['rolling_pct']:.1f}%")
    print()
    
    # Acceleration simulation
    print("[ACCELERATION] Acceleration Simulation (0-100 km/h)")
    print("-" * 70)
    
    accel_data = perf_calc.simulate_acceleration(
        power_watts=power_watts,
        target_velocity_kmh=100.0,
        length=geometry['dimensions']['length'],
        scale_mode='full_scale'
    )
    
    if accel_data['success']:
        print(f"Time to 100 km/h: {accel_data['time_seconds']:.2f} seconds")
        print(f"Average Acceleration: {accel_data['average_acceleration_ms2']:.2f} m/s²")
        print()
        
        # Show velocity progression
        print("Velocity Progression:")
        time_points = [0, 2, 4, 6, 8, 10]
        for t in time_points:
            if t < len(accel_data['time_history']):
                idx = min(int(t / 0.1), len(accel_data['velocity_history_kmh']) - 1)
                v = accel_data['velocity_history_kmh'][idx]
                print(f"  t = {t:2d}s: {v:5.1f} km/h")
    else:
        print(accel_data['message'])
    
    print()
    
    # Material comparison
    print("[MATERIALS] Material Comparison")
    print("-" * 70)
    
    material_comparison = perf_calc.compare_materials(
        power_watts=power_watts,
        length=geometry['dimensions']['length'],
        scale_mode='full_scale'
    )
    
    print(f"{'Material':<15} {'Mass (kg)':<12} {'Top Speed':<12} {'0-100 km/h':<12}")
    print("-" * 70)
    
    for material, data in material_comparison.items():
        mass_str = f"{data['mass_kg']:.0f}"
        top_speed_str = f"{data['top_speed_kmh']:.1f} km/h"
        accel_str = f"{data['acceleration_0_100_sec']:.2f} s" if data['success'] else "N/A"
        
        print(f"{material.replace('_', ' ').title():<15} {mass_str:<12} {top_speed_str:<12} {accel_str:<12}")
    
    print()
    
    # Scale comparison
    print("[SCALE] Scale Comparison (Miniature vs Full-Scale)")
    print("-" * 70)
    
    scale_comp = perf_calc.scale_comparison(
        power_watts=power_watts,
        miniature_length=0.25,  # 25cm model
        full_scale_length=geometry['dimensions']['length']
    )
    
    print(f"{'Property':<30} {'Miniature':<20} {'Full-Scale':<20}")
    print("-" * 70)
    print(f"{'Length':<30} {scale_comp['miniature']['length_m']:.2f} m{'':<16} {scale_comp['full_scale']['length_m']:.2f} m")
    print(f"{'Reynolds Number':<30} {scale_comp['miniature']['reynolds_number']:.2e}{'':<8} {scale_comp['full_scale']['reynolds_number']:.2e}")
    print(f"{'Cd (corrected)':<30} {scale_comp['miniature']['cd_corrected']:.3f}{'':<16} {scale_comp['full_scale']['cd_corrected']:.3f}")
    print(f"{'Top Speed':<30} {scale_comp['miniature']['top_speed_kmh']:.1f} km/h{'':<11} {scale_comp['full_scale']['top_speed_kmh']:.1f} km/h")
    print(f"{'Drag @ 100 km/h':<30} {scale_comp['miniature']['drag_force_100kmh_n']:.1f} N{'':<14} {scale_comp['full_scale']['drag_force_100kmh_n']:.1f} N")
    
    print()
    print(f"Cd Difference: {scale_comp['comparison']['cd_difference_pct']:.1f}%")
    print(f"Reynolds Ratio: {scale_comp['comparison']['reynolds_ratio']:.1f}×")
    
    print()
    
    # Complete summary
    print("[SUMMARY] Complete Performance Summary")
    print("-" * 70)
    
    summary = perf_calc.get_performance_summary(
        power_hp=power_hp,
        length=geometry['dimensions']['length'],
        scale_mode='full_scale'
    )
    
    print(json.dumps(summary, indent=2))
    
    print()
    print("=" * 70)
    print("[COMPLETE] Demo Complete!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Test with real STL files")
    print("3. Integrate with FastAPI backend")
    print()


def demo_with_stl(stl_filepath: str):
    """
    Demo with actual STL file
    
    Args:
        stl_filepath: Path to STL file
    """
    from stl_parser import STLParser
    from geometry_analyzer import GeometryAnalyzer
    from drag_estimator import DragEstimator
    from performance_calc import PerformanceCalculator
    
    print("=" * 70)
    print(f"ANALYZING STL FILE: {Path(stl_filepath).name}")
    print("=" * 70)
    print()
    
    # Load and validate STL
    print("[LOADING] Loading STL File...")
    parser = STLParser(stl_filepath)
    mesh_data = parser.load()
    
    stats = parser.get_stats()
    print(f"  Triangles: {stats['num_triangles']:,}")
    print(f"  File Size: {stats['file_size_mb']:.2f} MB")
    print()
    
    # Validate mesh
    print("[VALIDATION] Validating Mesh...")
    validation = parser.validate()
    print(f"  Quality Score: {validation['quality_score']:.1f}/100")
    print(f"  Valid: {'Yes' if validation['is_valid'] else 'No'}")
    
    if validation['issues']:
        print("  Issues:")
        for issue in validation['issues']:
            print(f"    - {issue}")
    
    if validation['warnings']:
        print("  Warnings:")
        for warning in validation['warnings']:
            print(f"    - {warning}")
    
    print()
    
    # Analyze geometry
    print("[GEOMETRY] Analyzing Geometry...")
    analyzer = GeometryAnalyzer(mesh_data)
    properties = analyzer.get_all_properties()
    
    print(f"  Length: {properties['dimensions']['length']:.2f} m")
    print(f"  Width: {properties['dimensions']['width']:.2f} m")
    print(f"  Height: {properties['dimensions']['height']:.2f} m")
    print(f"  Frontal Area: {properties['frontal_area_m2']:.2f} m²")
    print(f"  Volume: {properties['volume_m3']:.2f} m³ (confidence: {properties['volume_confidence']:.0%})")
    print(f"  Surface Area: {properties['surface_area_m2']:.2f} m²")
    print()
    
    # Estimate drag
    print("[DRAG] Estimating Drag Coefficient...")
    drag_est = DragEstimator(mesh_data, properties['frontal_area_m2'])
    analysis = drag_est.get_detailed_analysis()
    
    print(f"  Estimated Cd: {analysis['estimated_cd']:.3f}")
    print(f"  Base Cd: {analysis['factors']['base_cd']:.3f}")
    print("  Correction Factors:")
    for factor_name, factor_value in analysis['factors'].items():
        if factor_name != 'base_cd':
            print(f"    {factor_name}: {factor_value:.3f}")
    print()
    
    # Calculate performance
    print("[PERFORMANCE] Calculating Performance...")
    perf = PerformanceCalculator(
        cd=analysis['estimated_cd'],
        frontal_area=properties['frontal_area_m2'],
        volume=properties['volume_m3'],
        material='aluminum'
    )
    
    summary = perf.get_performance_summary(power_hp=150)
    
    print(f"  Mass: {summary['vehicle_specs']['mass_kg']:.0f} kg")
    print(f"  Top Speed: {summary['top_speed']['speed_kmh']:.1f} km/h")
    print(f"  0-100 km/h: {summary['acceleration']['0_100_kmh_sec']:.2f} seconds")
    print()
    
    print("=" * 70)
    print("[COMPLETE] Analysis Complete!")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Run with STL file
        stl_file = sys.argv[1]
        if Path(stl_file).exists():
            demo_with_stl(stl_file)
        else:
            print(f"Error: File not found: {stl_file}")
    else:
        # Run synthetic demo
        demo_without_stl()
