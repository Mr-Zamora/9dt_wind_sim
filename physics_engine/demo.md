======================================================================
AEROCLASS PHYSICS ENGINE DEMO
======================================================================        

📐 Vehicle Geometry (Synthetic Data)
----------------------------------------------------------------------        
dimensions:
  length: 4.52 m
  width: 1.83 m
  height: 1.41 m
frontal_area_m2: 2.14
volume_m3: 3.87
surface_area_m2: 28.30

🌪️  Drag Coefficient Estimation
----------------------------------------------------------------------        
Estimated Cd: 0.290
Classification: Good (sedan-like aerodynamics)

Feature Analysis:
  fineness_ratio: 3.20
  nose_radius: 0.12
  rear_taper_angle: 5.00
  surface_smoothness: 0.85
  underbody_flatness: 0.75

⚡ Performance Analysis
----------------------------------------------------------------------        
Material: Aluminum
Mass: 10449 kg

Engine Power: 150 HP (111.9 kW)

Top Speed Analysis:
  Predicted Top Speed: 172.2 km/h (47.8 m/s)
  Reynolds Number: 1.46e+07
  Cd (Reynolds corrected): 0.267
  Drag Force @ Top Speed: 800 N

Power Breakdown at Top Speed:
  Aerodynamic Drag: 34.2%
  Rolling Resistance: 65.8%

🚀 Acceleration Simulation (0-100 km/h)
----------------------------------------------------------------------        
Time to 100 km/h: 51.36 seconds
Average Acceleration: 0.54 m/s²

Velocity Progression:
  t =  0s:   0.0 km/h
  t =  2s:  22.6 km/h
  t =  4s:  32.5 km/h
  t =  6s:  39.7 km/h
  t =  8s:  45.7 km/h
  t = 10s:  50.8 km/h

🔬 Material Comparison
----------------------------------------------------------------------        
Material        Mass (kg)    Top Speed    0-100 km/h  
----------------------------------------------------------------------        
Carbon Fiber    6772         197.0 km/h   29.28 s
Aluminum        10449        172.2 km/h   51.36 s
Steel           30380        86.2 km/h    N/A
Abs Plastic     4025         216.6 km/h   16.13 s
Balsa Wood      503          242.5 km/h   3.69 s

📏 Scale Comparison (Miniature vs Full-Scale)
----------------------------------------------------------------------        
Property                       Miniature            Full-Scale
----------------------------------------------------------------------        
Length                         0.25 m                 4.52 m
Reynolds Number                7.88e+05         1.46e+07
Cd (corrected)                 0.304                 0.267
Top Speed                      167.6 km/h            172.2 km/h
Drag @ 100 km/h                308.0 N               269.8 N

Cd Difference: -12.4%
Reynolds Ratio: 18.6×

📊 Complete Performance Summary
----------------------------------------------------------------------        
{
  "vehicle_specs": {
    "mass_kg": 10449.0,
    "material": "aluminum",
    "cd": 0.29,
    "frontal_area_m2": 2.14,
    "volume_m3": 3.87,
    "length_m": 4.52,
    "scale_mode": "full_scale"
  },
  "powertrain": {
    "power_hp": 150,
    "power_kw": 111.855
  },
  "top_speed": {
    "speed_kmh": 172.23148186088662,
    "speed_mph": 107.04256175319243,
    "reynolds_number": 14635446.824182464,
    "cd_at_top_speed": 0.2668,
    "drag_force_n": 800.4344399097847
  },
  "acceleration": {
    "0_60_kmh_sec": 15.559999999999713,
    "0_100_kmh_sec": 51.35999999999835,
    "average_acceleration_ms2": 0.540844582900675
  },
  "efficiency": {
    "aero_power_pct": 34.23579379011295,
    "rolling_power_pct": 65.76421355173665,
    "power_to_weight_ratio": 10.704852138960666
  }
}

======================================================================        
✅ Demo Complete!
======================================================================        

Next Steps:
1. Install dependencies: pip install -r requirements.txt
2. Test with real STL files
3. Integrate with FastAPI backend
