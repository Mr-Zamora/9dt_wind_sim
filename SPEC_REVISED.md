# Software Requirements Specification (SRS) - REVISED
## Project AeroClass: Cloud-Native 3D Aerodynamic Simulator & STEM Analytics Dashboard

---

## 0. Implementation Status & Development Plan

### Current Progress (Updated: May 22, 2026)

#### ✅ Completed
- **Specification Review & Revision** (v2.0)
  - Replaced unrealistic Navier-Stokes solver with panel method approach
  - Added Reynolds number corrections for dual-scale system
  - Defined accuracy targets (15-25% error tolerance)
  - Established phased development roadmap
  
- **Frontend UI Prototype** (HTML/CSS)
  - 5 complete pages with inline CSS (no dependencies)
  - `index.html` - Landing page with upload zone, recent designs, quick start guide
  - `simulator.html` - 3-column layout with controls, 3D viewport placeholder, results panel
  - `results.html` - Detailed metrics display, pressure visualization, material comparison
  - `leaderboard.html` - Class rankings table with student stats
  - `classroom.html` - Teacher dashboard with class statistics
  - Modern gradient UI (purple/blue theme), fully responsive
  - Interactive controls (sliders, toggles) with JavaScript value updates
  - Located in: `/UI_test/`

#### 🚧 In Progress
- **Physics Engine (Python)** - Current Phase
  - Core computational modules for aerodynamic calculations
  - Standalone Python implementation (no web framework dependencies)
  - Will be wrapped with FastAPI in later phase

#### 📋 Planned Next Steps

**Phase 1: Core Physics Engine (Weeks 1-4)**
```
/physics_engine/
  ├── stl_parser.py          # STL file loading and validation
  ├── geometry_analyzer.py   # Frontal area, volume, bounding box
  ├── drag_estimator.py      # Quick preview Cd calculation
  ├── performance_calc.py    # Top speed, acceleration, Reynolds corrections
  ├── mesh_validator.py      # Mesh quality checks and repair
  ├── test_samples/          # Sample STL files for validation
  ├── tests/                 # Unit tests for all modules
  └── demo.py               # CLI demonstration script
```

**Dependencies:**
- `numpy` - Numerical computations
- `numpy-stl` - STL file parsing
- `scipy` - Scientific calculations
- `trimesh` - 3D mesh processing and analysis
- `pytest` - Testing framework

**Phase 2: FastAPI Backend (Weeks 5-8)**
```
/backend/
  ├── main.py               # FastAPI application entry point
  ├── routers/
  │   ├── designs.py        # Design upload and management
  │   ├── simulations.py    # Simulation execution endpoints
  │   ├── classrooms.py     # Classroom management
  │   └── auth.py          # Authentication
  ├── models/              # Pydantic data models
  ├── database/            # PostgreSQL connection and schemas
  ├── services/            # Business logic layer
  │   └── physics_service.py  # Wrapper for physics engine
  └── requirements.txt
```

**Phase 3: Frontend Integration (Weeks 9-12)**
- Three.js integration for 3D STL rendering
- API client implementation (fetch calls)
- Real-time simulation progress (WebSocket)
- File upload with progress indicators
- Results visualization with actual data

**Phase 4: Database & Authentication (Weeks 13-16)**
- PostgreSQL schema implementation
- User authentication (Auth0/Firebase)
- Classroom management system
- Design version tracking
- Leaderboard data persistence

**Phase 5: Production Deployment (Weeks 17-20)**
- Docker containerization
- Cloud deployment (AWS/Azure/GCP)
- S3/Blob storage for STL files
- Redis caching layer
- CI/CD pipeline setup

### Technology Stack (Finalized)

**Frontend:**
- HTML5/CSS3/JavaScript (ES6+)
- Three.js (3D rendering)
- React (future migration from static HTML)
- TailwindCSS (future styling framework)

**Backend:**
- FastAPI (Python 3.10+)
- Uvicorn (ASGI server)
- PostgreSQL 15+ (primary database)
- Redis (caching and job queue)
- Celery (async task processing)

**Physics Engine:**
- Python 3.10+
- NumPy (numerical arrays)
- SciPy (scientific computing)
- Trimesh (mesh processing)
- NumPy-STL (STL file I/O)

**Infrastructure:**
- Docker (containerization)
- AWS S3 / Azure Blob (file storage)
- Optional: AWS EC2 GPU instances (detailed analysis mode)
- GitHub Actions (CI/CD)

### Development Principles

1. **Modular Architecture** - Physics engine independent of web framework
2. **Test-Driven** - Unit tests for all calculation modules
3. **Educational Focus** - Code clarity over micro-optimization
4. **Progressive Enhancement** - Start simple, add complexity incrementally
5. **Validation First** - Benchmark against known shapes before complex geometries

---

## 1. Executive Summary & Purpose
Project AeroClass is an educational, cloud-native Software-as-a-Service (SaaS) application designed for secondary and vocational school STEM classrooms. The application bridges the gap between Computer-Aided Design (CAD) and physical engineering by allowing students to upload 3D vehicle designs exported from platforms like Onshape (via `.stl` format) into a browser-based, virtual wind tunnel. 

The application computes aerodynamic forces using **simplified computational methods optimized for educational accuracy**, maps aerodynamic high/low-pressure zones as surface color spectrums (heat maps), visualizes particle streamlines, and provides an advanced analytics dashboard. This dashboard evaluates the vehicle's top speed and acceleration under two distinct operational scales: **As-Modeled Miniature** (e.g., 3D prints, CO2 racers) and **1:1 Real-World Scale** (applying material physics, structural mass estimations, Reynolds number corrections, and realistic powertrain configurations).

**Accuracy Target**: Results within 15-25% of professional CFD simulations, sufficient for comparative educational analysis and design iteration learning.

---

## 2. System Architecture & High-Level Workflow

### 2.1 Architecture Overview
The system utilizes a **hybrid client-server architecture** balancing browser interactivity with cloud computational power.

```
[Student CAD (Onshape)] ➔ [Export .STL] ➔ [AeroClass Web UI Frontend]
                                                  │
   ┌──────────────────────────────────────────────┴──────────────────────────────┐
   ▼                                                                             ▼
[Module 1: Geometry Ingestion]                                      [Module 4: UI & Configuration]
   │ ── STL Upload & Validation                                                 │ ── Scale Toggle (Mini vs 1:1)
   │ ── Mesh Repair Pipeline                                                    │ ── Material Densities
   │ ── Frontal Area (Ray-Casting)                                              │ ── Power Inputs (HP / kW)
   │ ── Volume Estimation (Voxel-Based)                                         │ ── Simulation Mode Selection
   ▼                                                                             ▼
[Module 2: Aerodynamics Engine]                                      [Module 5: Performance Core]
   │ ── Panel Method Solver (WebAssembly)                                       │ ── Reynolds Number Correction
   │ ── Empirical Drag Database                                                 │ ── Top Speed Calculator
   │ ── Pressure Field Approximation                                            │ ── 0-100 km/h Drag Simulator
   ▼                                                                             ▼
[Module 3: Visualization Engine]                                     [Module 6: Cloud Services]
   │ ── WebGL Rendering (Three.js)                                              │ ── PostgreSQL (User Data)
   │ ── Pressure Heatmap Shader                                                 │ ── S3 Storage (STL Files)
   │ ── Pre-computed Streamlines                                                │ ── Optional GPU Compute
   └── Interactive 3D Controls                                                  └── Classroom Management API
```

### 2.2 Computation Strategy
- **Quick Preview Mode** (10-15 seconds): Geometric drag estimation + empirical corrections
- **Detailed Analysis Mode** (45-60 seconds): Panel method solver with boundary layer approximation
- **Client-Side**: Geometry processing, visualization, basic calculations
- **Server-Side**: Heavy physics computations, result caching, classroom data management

---

## 3. Functional Specifications by Module

### Module 1: Geometry Ingestion & Validation

#### 1.1 STL Upload Interface
- **Drag-and-Drop Ingestion**: Web-based multipart upload supporting binary and ASCII `.stl` files up to 100MB or 1,000,000 polygons
- **Progress Indicators**: Real-time upload progress with file size validation
- **Format Detection**: Automatic detection of binary vs ASCII STL format

#### 1.2 Mesh Validation & Repair Pipeline
**Validation Checks**:
- Non-manifold edges detection
- Unclosed shells (hole detection)
- Inverted surface normals
- Degenerate triangles (zero-area faces)
- Self-intersecting geometry

**Automated Repair**:
- **Level 1 (Auto-fix)**: Normal flipping, degenerate triangle removal
- **Level 2 (Assisted)**: Small hole filling (<5% surface area), duplicate vertex merging
- **Level 3 (Manual)**: Large defects flagged with visual highlighting, guidance to return to CAD

**User Feedback**:
```
✓ Mesh Quality: 94% (Excellent)
⚠ Minor Issues Auto-Repaired:
  - 12 inverted normals corrected
  - 3 degenerate triangles removed
✗ Critical Issue Detected:
  - Large opening in rear bumper (23 cm²)
  → Recommendation: Close gap in Onshape and re-export
```

#### 1.3 Geometric Analysis

**Automatic Bounding Box**:
- Calculates physical boundaries: $X_{width}$, $Y_{height}$, $Z_{length}$
- Auto-detects vehicle orientation (longest axis = length)
- Provides rotation tools if orientation incorrect

**Frontal Area Calculation ($A$)** - *IMPROVED METHOD*:
```python
# Ray-casting silhouette projection
def calculate_frontal_area(mesh, direction=[0,0,1]):
    """
    1. Project all triangles onto plane perpendicular to flow direction
    2. Use 2D polygon clipping to resolve overlaps
    3. Sum areas of non-overlapping projected regions
    4. Return area in m² with ±2% accuracy
    """
    projected_triangles = project_mesh_to_plane(mesh, direction)
    silhouette_polygon = compute_2d_union(projected_triangles)
    return calculate_polygon_area(silhouette_polygon)
```

**Volume Estimation ($V$)** - *ROBUST METHOD*:
```python
# Voxel-based volume calculation (tolerant to minor defects)
def calculate_volume(mesh, voxel_resolution=2mm):
    """
    1. Create 3D voxel grid encompassing mesh
    2. Mark voxels as inside/outside using ray-casting
    3. Sum interior voxel volumes
    4. Provide confidence score based on mesh quality
    """
    voxel_grid = create_voxel_grid(mesh.bounds, voxel_resolution)
    interior_voxels = flood_fill_exterior(voxel_grid, mesh)
    volume = count_voxels(interior_voxels) * voxel_resolution³
    confidence = assess_mesh_watertightness(mesh)
    return volume, confidence
```

**Output Display**:
```
Geometric Properties:
- Dimensions: 4.52m (L) × 1.83m (W) × 1.41m (H)
- Frontal Area: 2.14 m²
- Volume: 3.87 m³ (Confidence: 98%)
- Surface Area: 28.3 m²
```

---

### Module 2: Aerodynamics Engine (Simplified Physics)

#### 2.1 Computational Approach Philosophy
**Educational Accuracy vs Industrial Precision**:
- Full Navier-Stokes CFD: Hours of computation, 1-3% error
- **AeroClass Panel Method**: 60 seconds, 15-25% error ✓ *Sufficient for learning*

#### 2.2 Virtual Wind Tunnel Setup
**Enclosure Generation**:
- Front clearance: $1.5 \times L$
- Rear clearance (wake zone): $3.5 \times L$
- Lateral/Vertical clearance: $1.5 \times W/H$
- Total domain: ~$6L \times 3W \times 3H$

**Boundary Conditions**:
- **Inlet**: Uniform velocity field, $0-150$ km/h ($0-41.6$ m/s)
- **Outlet**: Atmospheric pressure ($0$ Pa gauge)
- **Walls**: Slip boundary (symmetry)
- **Floor**: Optional moving ground plane (velocity-matched)
- **Vehicle Surface**: No-slip wall

#### 2.3 Solver Implementation

**Quick Preview Mode (10-15s)**:
```python
def quick_drag_estimate(mesh, velocity, frontal_area):
    """
    Empirical drag estimation based on geometric features
    """
    # Analyze geometric features
    features = {
        'nose_radius': measure_leading_edge_curvature(mesh),
        'rear_taper_angle': measure_rear_angle(mesh),
        'surface_smoothness': calculate_surface_roughness(mesh),
        'underbody_flatness': analyze_underbody(mesh),
        'wheel_exposure': detect_wheel_wells(mesh)
    }
    
    # Base Cd from lookup table
    base_cd = empirical_cd_database.lookup(features)
    
    # Apply corrections
    cd_corrected = apply_feature_corrections(base_cd, features)
    
    # Calculate drag force
    drag_force = 0.5 * ρ_air * velocity² * cd_corrected * frontal_area
    
    return cd_corrected, drag_force
```

**Detailed Analysis Mode (45-60s)**:
```python
def panel_method_solver(mesh, velocity, moving_floor=True):
    """
    3D Panel Method (Potential Flow + Boundary Layer Correction)
    Compiled to WebAssembly for performance
    """
    # 1. Discretize surface into panels (~5000-10000 panels)
    panels = discretize_surface(mesh, target_count=7500)
    
    # 2. Solve potential flow (inviscid)
    #    ∇²φ = 0 with boundary conditions
    influence_matrix = build_influence_matrix(panels)
    velocities = solve_linear_system(influence_matrix, freestream=velocity)
    
    # 3. Calculate pressure distribution (Bernoulli)
    #    P = P_∞ + 0.5 * ρ * (V_∞² - V_local²)
    pressures = calculate_pressure_field(velocities, velocity)
    
    # 4. Boundary layer correction (empirical)
    #    Accounts for viscous drag not captured by potential flow
    viscous_correction = estimate_skin_friction(mesh, velocity)
    
    # 5. Integrate forces
    pressure_drag = integrate_pressure_forces(panels, pressures)
    total_drag = pressure_drag + viscous_correction
    
    cd = (2 * total_drag) / (ρ_air * velocity² * frontal_area)
    
    return cd, total_drag, pressures
```

#### 2.4 Computational Grid Strategy
**Fixed Resolution Approach** (not adaptive):
- Surface panels: 5,000-10,000 (based on mesh complexity)
- Panel size: Automatically scaled to vehicle dimensions
- No boundary layer refinement (too expensive)
- Trade-off: Speed over precision

---

### Module 3: Visualization & Post-Processing

#### 3.1 Surface Pressure Heat Map
**Rendering Pipeline**:
```javascript
// WebGL shader for pressure visualization
const pressureColorShader = `
  uniform float minPressure;
  uniform float maxPressure;
  varying float pressure;
  
  void main() {
    // Normalize pressure to [0, 1]
    float t = (pressure - minPressure) / (maxPressure - minPressure);
    
    // Color mapping (blue → cyan → green → yellow → red)
    vec3 color = mix(
      vec3(0.0, 0.0, 1.0),  // Deep blue (low pressure)
      vec3(1.0, 0.0, 0.0),  // Bright red (high pressure)
      t
    );
    
    gl_FragColor = vec4(color, 1.0);
  }
`;
```

**Pressure Zones**:
- **Red/Magenta** ($P > +500$ Pa): Stagnation zones (front bumper, grille)
- **Yellow/Green** ($-100$ to $+500$ Pa): Moderate pressure regions
- **Blue/Violet** ($P < -100$ Pa): Low pressure (roof, rear wake)

**Interactive Features**:
- Click on surface to view local pressure value
- Toggle heat map on/off
- Adjust color scale sensitivity

#### 3.2 Streamline Visualization
**Pre-Computed Approach** (not real-time):
```python
def generate_streamlines(velocity_field, num_lines=50):
    """
    Compute streamline paths after solver completes
    """
    # Seed particles at inlet grid
    seed_points = create_inlet_grid(spacing=0.2m, count=num_lines)
    
    # Integrate particle paths using RK4
    streamlines = []
    for seed in seed_points:
        path = integrate_streamline(
            start=seed,
            velocity_field=velocity_field,
            max_steps=1000,
            dt=0.01
        )
        streamlines.append(path)
    
    return streamlines
```

**Visualization**:
- Animated particles following pre-computed paths
- Color-coded by velocity magnitude
- Adjustable playback speed
- Individual streamline selection for detailed analysis

#### 3.3 Cutting Plane Tool
**Interactive Slice View**:
- Movable plane along X, Y, or Z axis
- Shows velocity vectors in cross-section
- Highlights vortex cores and separation zones
- Side-by-side comparison with 3D view

---

### Module 4: Materials, Scaling & Configuration

#### 4.1 Dual-Scale System with Reynolds Correction

**Scale Modes**:
1. **Miniature Scale (As-Modeled)**:
   - Uses native STL dimensions (typically 10-30 cm)
   - Reynolds number: $Re = 10^4 - 10^5$ (laminar/transitional)
   - Higher drag coefficients due to scale effects

2. **1:1 Real-World Scale**:
   - Automatic scaling to 4.5m baseline length
   - Reynolds number: $Re > 10^6$ (fully turbulent)
   - Lower drag coefficients (more realistic)

**Reynolds Number Correction** - *NEW*:
```python
def apply_reynolds_correction(cd_base, scale_mode, velocity, length):
    """
    Correct drag coefficient for Reynolds number effects
    """
    # Calculate Reynolds number
    Re = (ρ_air * velocity * length) / μ_air
    
    if scale_mode == "miniature":
        # Miniature models have higher Cd due to laminar flow
        if Re < 1e5:
            cd_corrected = cd_base * 1.25  # +25% drag penalty
        elif Re < 5e5:
            cd_corrected = cd_base * 1.15  # +15% drag penalty
        else:
            cd_corrected = cd_base * 1.05  # +5% drag penalty
    
    elif scale_mode == "full_scale":
        # Full-scale benefits from turbulent boundary layer
        if Re > 1e6:
            cd_corrected = cd_base * 0.92  # -8% drag reduction
        else:
            cd_corrected = cd_base
    
    return cd_corrected, Re
```

**Educational Display**:
```
Scale Comparison:
┌─────────────────┬──────────────┬──────────────┐
│                 │  Miniature   │  Full-Scale  │
├─────────────────┼──────────────┼──────────────┤
│ Length          │  0.25 m      │  4.50 m      │
│ Reynolds Number │  6.8 × 10⁴   │  1.2 × 10⁷   │
│ Cd (corrected)  │  0.38        │  0.29        │
│ Drag @ 100 km/h │  0.12 N      │  340 N       │
└─────────────────┴──────────────┴──────────────┘

💡 Notice: Miniature Cd is 31% higher due to laminar flow effects!
```

#### 4.2 Material Selection & Mass Calculation

**Material Database**:
| Material | Density (kg/m³) | Educational Context | Cost Factor |
|:---------|:----------------|:--------------------|:------------|
| **Carbon Fiber Composite** | 1,750 | Hypercars, F1 racing | 50× |
| **Aluminum 6061-T6** | 2,700 | Sports cars, aircraft | 3× |
| **Mild Steel** | 7,850 | Traditional vehicles | 1× |
| **ABS Plastic** | 1,040 | 3D prints, prototypes | 2× |
| **Balsa Wood** | 130 | CO2 dragsters | 5× |
| **Custom** | User Input | Advanced projects | - |

**Mass Calculation with Scaling**:
```python
def calculate_mass(volume, material_density, scale_factor):
    """
    Compute structural mass with cubic scaling law
    
    IMPORTANT: Vehicles are hollow shells, not solid blocks.
    We apply a structural factor to estimate actual material volume.
    Typical vehicles use 10-15% of bounding box volume as material.
    """
    # Structural factor: 12% of volume is actual material
    # (body panels, frame, interior components)
    structural_factor = 0.12
    
    if scale_factor == 1.0:  # Miniature
        mass = volume * material_density * structural_factor
    else:  # Full-scale
        # Volume scales as L³
        scaled_volume = volume * (scale_factor ** 3)
        mass = scaled_volume * material_density * structural_factor
    
    return mass
```

**Structural Factor Rationale**:
- **Bounding Box Volume**: Total 3D space occupied by vehicle
- **Actual Material Volume**: ~12% (hollow body, interior space, windows)
- **Example**: 3.87 m³ bounding box → 0.46 m³ actual material
- **Aluminum**: 0.46 m³ × 2,700 kg/m³ = **1,254 kg** ✓ (realistic sedan mass)

**Output Example**:
```
Material: Carbon Fiber Composite
- Bounding Volume: 3.87 m³
- Material Volume: 0.46 m³ (12% structural factor)
- Miniature Mass: 0.068 kg (68 grams)
- Full-Scale Mass: 1,247 kg
- Weight Savings vs Steel: 4,823 kg (79%)
```

#### 4.3 Manual Override Options
**For Non-Manifold Meshes**:
- Manual mass input field
- Manual frontal area override
- Confidence warnings displayed

---

### Module 5: Performance Analytics Dashboard

#### 5.1 Core Calculations

**Drag Force Output**:
$$F_d = \frac{1}{2} \rho_{air} \cdot v^2 \cdot C_d \cdot A$$

Where:
- $\rho_{air} = 1.225 \text{ kg/m}^3$ (sea level, 15°C)
- $v$ = velocity (m/s)
- $C_d$ = drag coefficient (computed)
- $A$ = frontal area (m²)

**Drag Coefficient**:
$$C_d = \frac{2 F_d}{\rho_{air} \cdot v^2 \cdot A}$$

#### 5.2 Top Speed Prediction
**Power Balance Method**:
```python
def calculate_top_speed(power_watts, cd, frontal_area, mass):
    """
    Find velocity where power output = power required to overcome drag
    P_engine = F_drag × v
    """
    # Solve: Power = 0.5 * ρ * v³ * Cd * A
    v_top = (2 * power_watts / (ρ_air * cd * frontal_area)) ** (1/3)
    
    # Apply rolling resistance correction
    rolling_resistance = 0.015 * mass * 9.81  # Crr = 0.015
    v_top_corrected = adjust_for_rolling_resistance(v_top, rolling_resistance)
    
    return v_top_corrected
```

**Example Output**:
```
Powertrain: 150 HP (112 kW)
Top Speed Analysis:
- Aerodynamic Limit: 247 km/h
- Rolling Resistance Penalty: -8 km/h
- Predicted Top Speed: 239 km/h

Breakdown at Top Speed:
- Aerodynamic Drag: 98.2 kW (87.7%)
- Rolling Resistance: 13.8 kW (12.3%)
```

#### 5.3 Acceleration Simulator (0-100 km/h)
**Time-Step Integration**:
```python
def simulate_acceleration(power, mass, cd, frontal_area, dt=0.01):
    """
    Iterative simulation from 0 to 100 km/h (27.78 m/s)
    """
    v = 0  # Initial velocity
    t = 0  # Time elapsed
    target_velocity = 27.78  # 100 km/h in m/s
    
    while v < target_velocity:
        # Calculate forces
        F_thrust = min(power / max(v, 1), 8000)  # Traction limit
        F_drag = 0.5 * ρ_air * v² * cd * frontal_area
        F_rolling = 0.015 * mass * 9.81
        
        # Net acceleration
        F_net = F_thrust - F_drag - F_rolling
        a = F_net / mass
        
        # Update velocity and time
        v += a * dt
        t += dt
        
        # Safety timeout
        if t > 60:
            return None  # Vehicle cannot reach 100 km/h
    
    return t
```

**Comparative Display**:
```
0-100 km/h Acceleration Times:
┌──────────────────┬──────────┬──────────┐
│ Material         │ Mass     │ Time     │
├──────────────────┼──────────┼──────────┤
│ Carbon Fiber     │ 1,247 kg │ 4.8 sec  │
│ Aluminum         │ 1,923 kg │ 6.2 sec  │
│ Steel            │ 6,070 kg │ 14.9 sec │
└──────────────────┴──────────┴──────────┘

💡 Insight: Reducing mass by 79% cuts acceleration time by 68%!
```

---

## 4. Classroom Features & Gamification

### 4.1 Classroom Leaderboard
**Sortable Metrics**:
- Lowest Drag Coefficient ($C_d$)
- Highest Top Speed ($v_{top}$)
- Fastest 0-100 km/h
- Best Power Efficiency (Top Speed / HP)
- Most Improved Design (version comparison)

**Display Format**:
```
🏆 Class Leaderboard - Lowest Drag Coefficient
┌──────┬─────────────────┬────────┬──────────────┬──────────┐
│ Rank │ Student         │ Cd     │ Design Name  │ Material │
├──────┼─────────────────┼────────┼──────────────┼──────────┤
│  🥇  │ Emma T.         │ 0.247  │ AeroSlice v3 │ CF       │
│  🥈  │ Liam K.         │ 0.263  │ StreamFlow   │ Al       │
│  🥉  │ Sofia R.        │ 0.281  │ WindCutter   │ CF       │
│  4   │ Noah P.         │ 0.295  │ SpeedDemon   │ Al       │
│  5   │ Ava M.          │ 0.312  │ RocketCar    │ Steel    │
└──────┴─────────────────┴────────┴──────────────┴──────────┘
```

### 4.2 STEM Lab Report Generator
**PDF Export Contents**:
1. **Cover Page**: Student name, design name, date
2. **Design Overview**:
   - Isometric renders (4 angles)
   - Pressure heat map overlay
   - Streamline visualization
3. **Geometric Data**:
   - Dimensions table
   - Frontal area, volume, mass
4. **Aerodynamic Results**:
   - Drag coefficient comparison chart
   - Reynolds number analysis
   - Scale comparison table
5. **Performance Metrics**:
   - Top speed prediction
   - Acceleration curve graph
   - Velocity vs Drag Force plot
6. **Engineering Reflection**:
   - Text box for student analysis
   - "What would you change?" prompts
   - Comparison to class average

### 4.3 Design Iteration Tracking
**Version History**:
- Store up to 5 design versions per student
- Side-by-side comparison tool
- Highlight improvements/regressions
- Export improvement timeline

---

## 5. System Infrastructure & Backend

### 5.1 Technology Stack

**Frontend**:
- **Framework**: React 18+ with TypeScript
- **3D Rendering**: Three.js + React Three Fiber
- **UI Components**: shadcn/ui + TailwindCSS
- **State Management**: Zustand
- **Physics Compute**: WebAssembly (Rust/C++)

**Backend**:
- **API Server**: Node.js (Express) or Python (FastAPI)
- **Database**: PostgreSQL 15+
- **File Storage**: AWS S3 / Azure Blob Storage
- **Caching**: Redis (simulation results)
- **Authentication**: Auth0 / Firebase Auth

**Optional GPU Compute**:
- **Platform**: AWS EC2 (g4dn instances) or Google Cloud GPU
- **Use Case**: Detailed analysis mode for complex geometries
- **Fallback**: Client-side WebAssembly if GPU unavailable

### 5.2 Database Schema

**Users Table**:
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  role ENUM('student', 'teacher', 'admin'),
  classroom_id UUID REFERENCES classrooms(id),
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Designs Table**:
```sql
CREATE TABLE designs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name VARCHAR(255),
  stl_file_url TEXT,
  version INTEGER DEFAULT 1,
  geometric_data JSONB,
  simulation_results JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Classrooms Table**:
```sql
CREATE TABLE classrooms (
  id UUID PRIMARY KEY,
  teacher_id UUID REFERENCES users(id),
  name VARCHAR(255),
  access_code VARCHAR(10) UNIQUE,
  settings JSONB
);
```

### 5.3 API Endpoints

**Design Management**:
- `POST /api/designs/upload` - Upload STL file
- `GET /api/designs/:id` - Retrieve design data
- `POST /api/designs/:id/simulate` - Run simulation
- `GET /api/designs/:id/results` - Get simulation results
- `DELETE /api/designs/:id` - Delete design

**Classroom**:
- `GET /api/classrooms/:id/leaderboard` - Get rankings
- `POST /api/classrooms/:id/join` - Student joins classroom
- `GET /api/classrooms/:id/students` - List students

**Export**:
- `POST /api/reports/generate` - Generate PDF report
- `GET /api/reports/:id/download` - Download PDF

---

## 6. User Experience & Error Handling

### 6.1 Error States & Guidance

**Mesh Validation Failures**:
```
❌ Critical Mesh Error Detected

Issue: Large opening in vehicle body (rear bumper)
Impact: Volume calculation unreliable, simulation may fail

Recommended Actions:
1. Return to Onshape
2. Close the gap using Loft or Fill tools
3. Re-export as STL
4. Re-upload to AeroClass

Alternative: Use manual mass override (Advanced)
```

**Simulation Convergence Issues**:
```
⚠️ Simulation Warning

The solver struggled to converge for this geometry.
Results may be less accurate than usual.

Possible Causes:
- Extremely complex surface details
- Very sharp edges or thin features
- Mesh quality issues

Suggestions:
- Simplify small details (<5mm)
- Add fillets to sharp corners (radius >10mm)
- Try Quick Preview mode for faster estimate
```

**Performance Guidance**:
```
💡 Design Improvement Tips

Your Cd = 0.342 (Class Average: 0.285)

High-drag areas detected:
1. Front bumper (flat surface) → Add nose taper
2. Rear window (abrupt cutoff) → Extend roofline
3. Wheel wells (exposed) → Add partial covers

Estimated Cd reduction potential: -0.05 to -0.08
```

### 6.2 Onboarding & Tutorials

**First-Time User Flow**:
1. Interactive tutorial with sample STL file
2. Guided tour of pressure heat maps
3. Explanation of Cd values (0.2 = excellent, 0.4 = poor)
4. Practice simulation with instant feedback

**Contextual Help**:
- Tooltips on all technical terms
- "What is Reynolds Number?" expandable cards
- Video tutorials embedded in UI
- Teacher resource library

---

## 7. Validation & Accuracy

### 7.1 Benchmark Test Cases

**Standard Shapes** (Known Cd values):
| Shape | Theoretical Cd | AeroClass Target | Tolerance |
|:------|:---------------|:-----------------|:----------|
| Sphere | 0.47 | 0.45-0.50 | ±6% |
| Cylinder | 1.17 | 1.10-1.25 | ±7% |
| Streamlined Body | 0.04 | 0.04-0.06 | ±50%* |
| Cube | 1.05 | 1.00-1.15 | ±10% |

*Streamlined bodies are challenging for simplified methods

**Real Vehicle Validation**:
- Tesla Model 3 (Cd = 0.23): Target 0.20-0.28
- Toyota Prius (Cd = 0.25): Target 0.22-0.30
- Jeep Wrangler (Cd = 0.45): Target 0.40-0.52

### 7.2 Accuracy Disclaimers

**Displayed to Students**:
```
ℹ️ Educational Simulation Notice

AeroClass uses simplified computational methods optimized 
for learning and design comparison. Results are typically 
within 15-25% of professional wind tunnel data.

✓ Excellent for: Comparing design iterations
✓ Good for: Understanding aerodynamic principles
✗ Not suitable for: Final engineering validation

For production vehicles, consult professional CFD services.
```

### 7.3 Uncertainty Quantification
**Result Display**:
```
Drag Coefficient: 0.287 ± 0.043
                  ↑       ↑
                  Value   Uncertainty (±15%)

Confidence Level: Medium
- Mesh Quality: Excellent (98%)
- Solver Convergence: Good
- Geometry Complexity: Moderate
```

---

## 8. Non-Functional Requirements

### 8.1 Performance Targets
- **Page Load**: <3 seconds (initial load)
- **STL Upload**: <10 seconds (50MB file)
- **Quick Preview**: 10-15 seconds
- **Detailed Analysis**: 45-60 seconds
- **3D Rendering**: 60 FPS on mid-tier hardware

### 8.2 Browser Compatibility
**Minimum Requirements**:
- Chrome 90+
- Safari 14+
- Edge 90+
- Firefox 88+

**Hardware Targets**:
- **Minimum**: Chromebook (4GB RAM, Intel Celeron)
- **Recommended**: Laptop (8GB RAM, Intel i5 / Apple M1)
- **Optimal**: Desktop (16GB RAM, dedicated GPU)

### 8.3 Scalability
- Support 30 concurrent students per classroom
- Handle 1,000 active users simultaneously
- Store 100,000 design files
- Process 10,000 simulations per day

### 8.4 Security & Privacy
- **Data Encryption**: TLS 1.3 for all connections
- **File Scanning**: Malware detection on STL uploads
- **Access Control**: Role-based permissions (student/teacher/admin)
- **Data Retention**: Student data deleted after 2 years (configurable)
- **GDPR Compliance**: Data export and deletion tools

### 8.5 Accessibility
- **WCAG 2.1 Level AA** compliance
- Screen reader support for all UI elements
- Keyboard navigation for 3D controls
- High-contrast mode for visualizations
- Closed captions for tutorial videos

---

## 9. Development Roadmap

### Phase 1: MVP (Months 1-6)
**Core Features**:
- ✓ STL upload and basic validation
- ✓ Quick Preview drag estimation
- ✓ Simplified pressure visualization
- ✓ Basic analytics dashboard (Cd, top speed)
- ✓ Single-scale mode (full-scale only)
- ✓ PDF report generation
- ✓ Teacher classroom management

**Technology**:
- React frontend with Three.js
- Empirical drag database
- PostgreSQL + S3 storage
- Basic authentication

### Phase 2: Enhanced Physics (Months 7-12)
**Advanced Features**:
- ✓ Panel method solver (WebAssembly)
- ✓ Dual-scale with Reynolds corrections
- ✓ Improved streamline visualization
- ✓ Classroom leaderboard
- ✓ Design iteration tracking
- ✓ Mesh repair pipeline

**Technology**:
- Rust/C++ compiled to WASM
- Redis caching layer
- Advanced mesh processing

### Phase 3: Production Ready (Months 13-18)
**Polish & Scale**:
- ✓ GPU-accelerated detailed mode
- ✓ Real-time collaboration features
- ✓ Mobile-responsive design
- ✓ Advanced analytics (lift, moment)
- ✓ Custom material database
- ✓ API for third-party integrations

**Technology**:
- Cloud GPU compute instances
- Microservices architecture
- CDN for global performance

---

## 10. Success Metrics

### Educational Impact
- **Student Engagement**: 80%+ completion rate for design projects
- **Learning Outcomes**: 70%+ students demonstrate understanding of Cd concept
- **Design Iteration**: Average 3+ versions per student
- **Classroom Adoption**: 100+ schools within first year

### Technical Performance
- **Simulation Accuracy**: 85%+ results within ±25% of benchmark
- **System Uptime**: 99.5%+ availability
- **User Satisfaction**: 4.5/5 average rating
- **Support Tickets**: <5% of simulations require assistance

---

## 11. Appendices

### Appendix A: Physics Equations Reference
[Detailed derivations of all formulas used]

### Appendix B: Material Properties Database
[Complete material specifications with sources]

### Appendix C: Benchmark Test Results
[Validation data for standard shapes]

### Appendix D: Teacher Guide
[Classroom integration strategies and lesson plans]

---

## Document Revision History
- **v2.1** (2026-05-22 PM): Implementation progress update
  - Added Section 0: Implementation Status & Development Plan
  - Documented completed UI prototype (5 HTML pages)
  - Finalized technology stack (FastAPI + Python physics engine)
  - Defined 5-phase development roadmap (20 weeks)
  - Established development principles and testing strategy
  
- **v2.0** (2026-05-22 AM): Major revision addressing feasibility concerns
  - Replaced Navier-Stokes with panel method + empirical corrections
  - Added Reynolds number scaling corrections
  - Improved mesh validation and volume calculation methods
  - Added system infrastructure specifications
  - Defined error handling and user guidance
  - Established accuracy targets and validation benchmarks
  
- **v1.0** (Original): Initial specification

---

**Document Status**: ✅ Specification Finalized | 🚧 Implementation In Progress (Phase 1)

**Current Phase**: Building Python Physics Engine (Standalone)

**Next Milestone**: Complete core aerodynamics calculation modules with unit tests
