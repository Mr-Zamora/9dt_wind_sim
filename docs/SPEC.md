# Software Requirements Specification (SRS)
## Project AeroClass: Cloud-Native 3D Aerodynamic Simulator & STEM Analytics Dashboard

---

## 1. Executive Summary & Purpose
Project AeroClass is an educational, cloud-native Software-as-a-Service (SaaS) application designed for secondary and vocational school STEM classrooms. The application bridges the gap between Computer-Aided Design (CAD) and physical engineering by allowing students to upload 3D vehicle designs exported from platforms like Onshape (via `.stl` format) into a browser-based, virtual wind tunnel. 

Unlike purely visual fluid simulators, this application computes real physical forces, maps aerodynamic high/low-pressure zones as surface color spectrums (heat maps), visualizes particle streamlines, and provides an advanced analytics dashboard. This dashboard evaluates the vehicle's top speed and acceleration under two distinct operational scales: **As-Modeled Miniature** (e.g., 3D prints, CO2 racers) and **1:1 Real-World Scale** (applying material physics, structural mass estimations, and realistic powertrain configurations).

---

## 2. System Architecture & High-Level Workflow
The system utilizes an decoupled, asynchronous architecture to ensure that heavy 3D rendering and scientific computations run fluidly without freezing user hardware or web browsers.

```
[Student CAD (Onshape)] ➔ [Export .STL] ➔ [AeroClass Web UI Frontend]
                                                  │
   ┌──────────────────────────────────────────────┴──────────────────────────────┐
   ▼                                                                             ▼
[Module 1: Geometry Ingestion]                                      [Module 4: UI & Configuration]
   │ ── Calculate Frontal Area (Silhouette Projection)                         │ ── Scale Toggle (Mini vs 1:1)
   ▼                                                                             │ ── Material Densities
[Module 2: Physics Engine & Mesh Generator]                                      │ ── Power Inputs (HP / kW)
   │ ── Discrete Computational Grid                                              ▼
   │ ── Native Navier-Stokes Approximation Fluid Solver             [Module 5: Performance Core]
   ▼                                                                             │ ── Top Speed Calculator
[Module 3: Post-Processor Visualization]                                         │ ── 0-100 km/h Drag Simulator
   │ ── Interactive WebGL Canvas (Three.js/Babylon.js)                           ▼
   └── Color Pressure Heatmaps & Streamline Generators              [Classroom Performance Leaderboard]
```

---

## 3. Functional Specifications by Module

### Module 1: Geometry Ingestion (The STL Handler)
* **Drag-and-Drop Ingestion:** Web-based multipart upload interface supporting binary and ASCII `.stl` files up to 100MB or 1,000,000 polygons.
* **Mesh Validation & Repair:** Auto-detection of non-manifold geometry, unclosed shells (holes), inverted surface normals, and degenerate triangles. Highlighting of fatal mesh errors to guide students back to Onshape for design revision.
* **Automatic Bounding Box Calculation:** Immediate calculation of the design's physical boundaries across the Cartesian coordinate system ($X_{width}, Y_{height}, Z_{length}$).
* **Silhouette Projection (Frontal Area $A$):**
    * The app projects a 2D orthographic parallel silhouette of the mesh from the direct front vector ($+Z$ or $+X$ depending on alignment).
    * It calculates the absolute cross-sectional surface area ($A$) in square meters ($m^2$) by computing the pixel-fill ratio or integrating bounding boundary loops. This $A$ value is locked into the global state for application-wide physics equations.

### Module 2: Physics Engine & Flow Simulation (The Wind Tunnel)
* **Virtual Enclosure Generation:** Automatically instantiates an air-volume bounding box centered around the imported car model.
    * *Sizing Rules:* Front clearance = $1.5 	imes L$, Rear clearance (wake capture zone) = $3.5 	imes L$, Lateral/Vertical clearance = $1.5 	imes W/H$ (where $L, W, H$ represent vehicle length, width, and height).
* **Boundary Condition Configuration Interface:**
    * **Inlet Velocity Slider:** Range: $0 - 150 	ext{ km/h}$ ($0 - 41.6 	ext{ m/s}$). Defines air entry velocity at the front enclosure face.
    * **Moving Floor Toggle:** Synchronizes the floor velocity with the inlet wind velocity to accurately simulate asphalt movement and eliminate boundary-layer friction anomalies underneath stationary tires.
    * **Outlet & Walls:** Static atmospheric pressure outlet ($0 	ext{ Pa}$ gauge) on the rear face; symmetry boundary conditions on the side and top faces.
* **Computational Grid Generator (Fluid Mesh):** Divides the enclosure into discrete volume coordinates. Automatically increases cell resolution near the surface boundary layers of the car mesh to capture fine aerodynamic details without blowing out calculation times.

### Module 3: Post-Processor & Visualizations
* **Surface Pressure Color Mapping (The "Heat Map"):**
    * Calculates local pressure gradients ($P$) across every triangle face on the vehicle shell.
    * Renders a continuous color spectrum across the 3D model using WebGL:
        * **Bright Red / Magenta:** Stagnation zones ($P_{max}$) where air velocity drops toward zero (e.g., vertical bumpers, un-filleted grilles).
        * **Deep Blue / Violet:** Low-pressure suction zones ($P_{min}$) where air accelerates drastically around sharp curves or breaks away, causing aerodynamic lift or high-drag trailing pockets.
* **Dynamic Streamline Particle System:**
    * Generates interactive, animated 3D visual lines originating from a grid layout at the inlet face.
    * Particles track along computed velocity vector fields ($u, v, w$) in real time.
    * Allows students to isolate individual particle streams to track vortices, boundary layer separation, and turbulent wake structures behind spoilers or wheel arches.
* **Interactive Cutting Plane (Slice Tool):** A movable 2D plane slider allowing the student to cut through the $X, Y,$ or $Z$ axes of the 3D space, mapping localized air velocity vectors directly around the vehicle profile.

### Module 4: Materials, Scaling, & Configuration
* **Dual-Scale Engine Toggle:**
    * `Miniature Scale (As Modeled):` Locks physics calculations directly to the native dimensions extracted from the STL file (typically matching 3D-printer envelopes, roughly $10	ext{ cm} - 30	ext{ cm}$ in length).
    * `1:1 Real-World Scale:` Applies an automatic isotropic upscaling multi-factor to expand the vehicle dimensions to realistic production vehicle sizes (standardized to a target baseline length of $4.5 	ext{ meters}$).
* **Material Matrix & Weight Calculation:**
    * Extracts the raw internal material volume ($V$) from the enclosed STL geometry.
    * Provides a material selection dropdown containing pre-loaded physical properties:
        | Material Selection | Density ($
ho_{mat}$) | Educational Context |
        | :--- | :--- | :--- |
        | **Carbon Fiber Composite** | $1,750 	ext{ kg/m}^3$ | Cutting-edge hypercars / aerospace |
        | **Aluminum (6061-T6)** | $2,700 	ext{ kg/m}^3$ | Premium sports cars / weight reduction |
        | **Mild Steel** | $7,850 	ext{ kg/m}^3$ | Traditional heavy consumer vehicles |
        | **ABS Plastic** | $1,040 	ext{ kg/m}^3$ | 3D-printed prototypes / interior panels |
        | **Balsa Wood** | $130 	ext{ kg/m}^3$ | Traditional CO2 dragster physical models |
    * **Mass Estimation ($M$):** Computes total structural mass using $M = V 	imes 
ho_{mat}$, applying structural scaling laws when switched to 1:1 scale (scaling volume by the cube of the length factor).

### Module 5: Analytics Dashboard & Performance Core
* **Aerodynamic Drag Force Output ($F_d$):** Integrates all local pressure and shear forces acting along the longitudinal axis ($X$) to output total drag resistance in Newtons ($N$).
* **Automated Drag Coefficient ($C_d$) Solver:** Solves the core aerodynamic equation in reverse based on simulation results:
    $$C_d = rac{2 F_d}{
ho_{air} \cdot v^2 \cdot A}$$
    *(Where $
ho_{air} = 1.225 	ext{ kg/m}^3$, $v = 	ext{inlet velocity}$, and $A = 	ext{calculated frontal area}$).*
* **Theoretical Top-Speed Predictor:**
    * Accepts user powertrain inputs via a Power Slider: Horsepower (HP) or Kilowatts (kW) ($1 	ext{ HP} = 745.7 	ext{ Watts}$).
    * Calculates the point of terminal equilibrium where maximum engine power output perfectly balances total aerodynamic resistance power ($P_{drag} = F_d \cdot v$).
    * **The System Equation:**
        $$v_{top} = \sqrt[3]{rac{2 \cdot 	ext{Power (Watts)}}{
ho_{air} \cdot C_d \cdot A}}$$
* **0–100 km/h Virtual Drag Simulator (The Standing Start):**
    * Executes an iterative mathematical time-step simulation ($dt = 0.01	ext{s}$) modeling a straight-line acceleration run from $0 	ext{ to } 100 	ext{ km/h}$ ($0 	ext{ to } 27.78 	ext{ m/s}$).
    * At each step, net instantaneous acceleration ($a$) is computed factoring in material weight and fluid drag:
        $$a = rac{F_{thrust} - F_{drag}}{M}$$
        *(Where $F_{thrust} = 	ext{Power} / v$, capped by a baseline mechanical tire traction limit, $F_{drag} = 0.5 \cdot 
ho_{air} \cdot v^2 \cdot C_d \cdot A$, and $M = 	ext{calculated material mass}$).*
    * **The Output:** Returns the precise elapsed time in seconds. Highlights how changing materials (e.g., Steel to Carbon Fiber) drastically slashes acceleration times despite keeping the exact same aerodynamic top speed.

---

## 4. Classroom Gamification & Data Exports
* **Classroom Leaderboard Integration:** A shared visual dashboard view where the educator can project a live ranking of the students' designs. Sortable by lowest Drag Coefficient ($C_d$), highest Theoretical Top Speed ($v_{top}$), or fastest 0-100 km/h acceleration.
* **STEM Lab Report PDF Exporter:** Generates a clean, presentation-ready PDF report containing:
    * Isometric visual renders of the car with its pressure heat map overlay.
    * Calculated metrics tables ($A, M, C_d, F_d$).
    * Line charts plotting *Velocity vs. Time* (the acceleration curve) and *Velocity vs. Drag Force*.
    * A student notation section for engineering reflection (e.g., outlining modifications required in Onshape version 2 to improve performance).

---

## 5. Non-Functional Requirements & Guardrails
* **Browser Interoperability:** Application must run fully without local extensions on Google Chrome, Apple Safari, Microsoft Edge, and Mozilla Firefox. Optimized to run fluidly on low-tier student hardware, such as school-issued Chromebooks.
* **Execution Limits:** Solvers must compute and return steady-state results within an execution ceiling of 60 seconds. This is achieved by utilizing pre-compiled mathematical approximations for fluid fields instead of industrial-grade hours-long differential equation solvers, fitting perfectly into standard 45-minute school class periods.
