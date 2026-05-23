# AeroClass - Complete Technical Analysis

## Project Summary

**AeroClass** is an educational aerodynamics simulator for STEM classrooms. Students upload 3D vehicle designs (STL files) to analyze drag coefficients, top speed, and acceleration in a virtual wind tunnel.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend (UI_test/)                           │
│     index.html (Unified Simulator) │ simulator.css │ simulator.js       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │ HTTP/REST
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend (backend/)                       │
│  main.py → routers/ (designs, simulations, health)                     │
│          → services/physics_service.py                                  │
│          → models/schemas.py (Pydantic)                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │ imports
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Physics Engine (physics_engine/)                    │
│  stl_parser.py → geometry_analyzer.py → drag_estimator.py              │
│                                       → performance_calc.py             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module Analysis

### 1. Physics Engine (`physics_engine/`)

| Module | Purpose | Key Methods | Status |
|--------|---------|-------------|--------|
| `stl_parser.py` | Load/validate STL files | `load()`, `validate()`, `get_stats()` | ✅ Complete |
| `geometry_analyzer.py` | Frontal area, volume, bounding box | `calculate_frontal_area()`, `calculate_volume_convex_hull()` | ✅ Complete |
| `drag_estimator.py` | Empirical Cd estimation | `estimate_cd_quick()`, `analyze_features()` | ✅ Complete |
| `performance_calc.py` | Top speed, acceleration, Reynolds | `calculate_top_speed()`, `simulate_acceleration()` | ✅ Complete |

**Key Design Decisions:**
- **Auto-unit detection**: Converts mm→m if max dimension > 5.0
- **Semantic axis detection**: Longest axis = length (nose-to-tail), regardless of STL orientation
- **Convex hull volume**: Fast (~5s) vs voxel method (30s+), 85% confidence
- **12% structural factor**: Vehicles are hollow shells, not solid blocks
- **Reynolds corrections**: Miniature +5-25% Cd penalty, full-scale -8% Cd reduction

### 2. FastAPI Backend (`backend/`)

| File | Endpoints | Purpose |
|------|-----------|---------|
| `routers/designs.py` | `POST /upload`, `GET /{id}`, `DELETE /{id}` | STL upload/management |
| `routers/simulations.py` | `POST /run`, `GET /{id}/materials`, `GET /{id}/scales` | Run simulations |
| `routers/health.py` | `GET /health`, `GET /ping` | Health checks |
| `services/physics_service.py` | - | Wraps physics engine |
| `models/schemas.py` | - | Pydantic request/response models |

**API Features:**
- CORS enabled (all origins for dev)
- Swagger UI at `/api/docs`
- Static files served from `/ui/`
- Numpy→Python type conversion for JSON serialization

### 3. Frontend (`UI_test/`)

| Page | Purpose |
|------|---------|
| `index.html` | Unified simulator landing page: controls, 3D viewport, results |
| `simulator.css` | Interactive prototype stylesheet |
| `simulator.js` | Interactive 3D OrbitControls, STLLoader, and simulation logic |

**Tech**: Pure HTML/CSS/JS (no framework), modern gradient UI, responsive design.

---

## Data Flow

```
1. Upload STL → POST /api/designs/upload
   └─ STLParser.load() → validate() → GeometryAnalyzer → DragEstimator
   └─ Returns: design_id, num_triangles, status

2. Run Simulation → POST /api/simulations/run
   └─ PhysicsService.analyze_stl() → run_simulation()
   └─ PerformanceCalculator: top_speed, acceleration, Reynolds correction
   └─ Returns: Cd, mass, top_speed, 0-100 time, power breakdown
```

---

## Key Algorithms

### Frontal Area Calculation
```python
# Project triangles onto plane perpendicular to flow
# Sum projected areas × 0.5 (closed mesh) × 0.7 (overlap correction)
# Cap at 82% of width × height
```

### Drag Coefficient Estimation
```python
base_cd = lookup(fineness_ratio)  # 0.25-0.45
cd *= nose_factor      # 0.95-1.10
cd *= rear_factor      # 0.90-1.05
cd *= smoothness_factor
cd *= underbody_factor
cd *= aspect_factor
```

### Top Speed (Power Balance)
```python
# Iterative: find v where P_engine = P_drag + P_rolling
v_top = (2 * power / (ρ * Cd * A)) ^ (1/3)  # Initial estimate
# Newton's method refinement with rolling resistance
```

### 0-100 km/h Acceleration
```python
# Time-step integration (dt=0.01s)
F_thrust = min(power/v, traction_limit)
F_drag = 0.5 * ρ * v² * Cd * A
a = (F_thrust - F_drag - F_rolling) / mass
```

---

## Error History (11 total, 10 fixed)

| # | Error | Root Cause | Fix |
|---|-------|------------|-----|
| 1 | UnicodeEncodeError | Windows cp1252 vs Unicode emoji | Removed emojis |
| 2 | Unrealistic mass (10,449 kg) | Solid volume assumption | 12% structural factor |
| 3 | KeyError 'length' | Circular dependency in features dict | Pass params directly |
| 4 | Slow volume calc | Voxel method too slow | Convex hull method |
| 5 | Blank UI screen | Static files mount order | API routes first |
| 6 | JSON numpy.float32 | FastAPI can't serialize numpy | `convert_numpy_types()` |
| 7 | JS not attaching | DOM not ready | `DOMContentLoaded` wrapper |
| 8 | Material dropdown null | Missing element IDs | Added `id` attributes |
| 9 | Design info 500 | Same as #6 | Applied conversion |
| 10 | Auto-reload stuck | WatchFiles issue | Manual restart (workaround) |
| 11 | Missing metric card | HTML/JS index mismatch | Added Vehicle Mass card |

---

## Current State

| Component | Status | Notes |
|-----------|--------|-------|
| Physics Engine | ✅ Complete | All 4 modules working |
| FastAPI Backend | ✅ Complete | All endpoints functional |
| Frontend UI | ✅ Prototype | Static HTML, needs Three.js integration |
| 3D Visualization | 📋 Planned | Three.js for STL rendering |
| Database | 📋 Planned | PostgreSQL for persistence |
| Authentication | 📋 Planned | Auth0/Firebase |

---

## Next Steps (Recommended)

1. **Three.js Integration** - Add 3D STL rendering to `index.html`
2. **Pressure heatmap visualization** - Color vertices by normal direction
3. **Unit tests** - pytest for physics engine validation
4. **Database** - PostgreSQL for design/user persistence
5. **WebSocket** - Real-time simulation progress

---

## Running the Project

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000/ui/

# Physics Engine Demo
cd physics_engine
python demo.py [optional: path/to/file.stl]
```
