# AeroClass

Educational aerodynamics simulator for STEM classrooms. Students upload 3D vehicle designs (STL files) to analyze drag coefficients, top speed, and acceleration in a virtual wind tunnel.


## Features

- **STL Upload & Validation**: Upload vehicle designs with automatic mesh quality checks
- **Aerodynamic Analysis**: Quick preview mode with empirical drag coefficient estimation
- **Performance Simulation**: Top speed prediction and 0-100 km/h acceleration simulation
- **Dual-Scale Analysis**: Compare miniature (as-modeled) vs full-scale (1:1) performance
- **Material Comparison**: Test performance across carbon fiber, aluminum, steel, ABS, and balsa wood
- **Reynolds Number Corrections**: Scale-dependent drag adjustments for educational accuracy
- **Interactive UI**: Modern web interface with real-time simulation results

## Project Structure

```
9dt_wind_sim/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── routers/               # API route handlers
│   ├── designs.py         # Design upload/management
│   ├── simulations.py     # Simulation endpoints
│   └── health.py          # Health checks
├── models/                # Pydantic schemas
│   └── schemas.py         # Request/response models
├── services/              # Business logic
│   └── physics_service.py # Physics engine wrapper
├── physics_engine/        # Core physics modules
│   ├── stl_parser.py      # STL loading/validation
│   ├── geometry_analyzer.py # Frontal area, volume
│   ├── drag_estimator.py  # Cd estimation
│   ├── performance_calc.py # Top speed, acceleration
│   └── demo.py           # CLI demonstration
├── UI_test/              # Frontend prototype
│   ├── index.html        # Main simulator & landing page
│   ├── simulator.css     # Styling for simulator
│   └── simulator.js      # Main interactive simulation logic
├── docs/                 # Documentation
│   ├── SPEC.md          # Original specification
│   ├── SPEC_REVISED.md  # Revised specification
│   ├── ERRORS.md        # Error tracking
│   └── TECH.md          # Technical analysis
├── stl_samples/         # Sample STL files
└── uploads/             # Runtime uploaded files
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd 9dt_wind_sim
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode

```bash
python main.py
```

The server will start at `http://localhost:8000`

- **API Documentation**: http://localhost:8000/api/docs (Swagger UI)
- **Web Interface**: http://localhost:8000/ui/index.html

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check
- `GET /api/health` - Server health status
- `GET /api/ping` - Simple ping test

### Design Management
- `POST /api/designs/upload` - Upload STL file
- `GET /api/designs/{design_id}` - Get design info
- `DELETE /api/designs/{design_id}` - Delete design
- `GET /api/designs/{design_id}/stl` - Download STL file

### Simulations
- `POST /api/simulations/run` - Run aerodynamic simulation
- `GET /api/simulations/{design_id}/materials` - Material comparison
- `GET /api/simulations/{design_id}/scales` - Scale comparison

## Physics Engine Demo

Run the physics engine independently for testing:

```bash
cd physics_engine
python demo.py                    # Synthetic data demo
python demo.py path/to/file.stl   # Test with actual STL file
```

## Usage Example

### 1. Upload a Design

```bash
curl -X POST "http://localhost:8000/api/designs/upload" \
  -F "file=@vehicle.stl"
```

Response:
```json
{
  "design_id": "abc123...",
  "filename": "vehicle.stl",
  "file_size_mb": 2.5,
  "num_triangles": 15000,
  "status": "ready"
}
```

### 2. Run Simulation

```bash
curl -X POST "http://localhost:8000/api/simulations/run" \
  -H "Content-Type: application/json" \
  -d '{
    "design_id": "abc123...",
    "simulation_mode": "quick_preview",
    "wind_speed_kmh": 100,
    "material": "aluminum",
    "engine_power_hp": 150,
    "scale_mode": "full_scale"
  }'
```

Response:
```json
{
  "simulation_id": "xyz789...",
  "design_id": "abc123...",
  "status": "completed",
  "estimated_cd": 0.29,
  "cd_corrected": 0.27,
  "reynolds_number": 12000000,
  "vehicle_mass_kg": 1254,
  "top_speed_kmh": 237.5,
  "acceleration_0_100_sec": 5.3,
  "drag_force_n": 340
}
```

## Materials Supported

| Material | Density (kg/m³) | Use Case |
|----------|----------------|----------|
| Foam Composite | 1,600 | Classroom models |
| Carbon Fiber | 1,750 | Hypercars, F1 |
| Aluminum | 2,700 | Sports cars |
| Steel | 7,850 | Traditional vehicles |
| ABS Plastic | 1,040 | 3D prints, prototypes |
| Balsa Wood | 130 | CO2 dragsters |

## Accuracy & Limitations

- **Target Accuracy**: 15-25% error vs professional CFD
- **Best For**: Comparative analysis, design iteration learning
- **Not For**: Final engineering validation, production vehicles

### Known Limitations
1. Simplified pressure field (no full Navier-Stokes)
2. No lift/downforce calculations
3. No wheel rotation effects
4. Simplified boundary layer modeling

## Deployment

### Docker (Recommended)

Create a `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t aeroclass .
docker run -p 8000:8000 aeroclass
```

### Cloud Deployment

**AWS/Azure/GCP**:
1. Deploy to a managed container service (ECS, AKS, Cloud Run)
2. Use S3/Blob Storage for STL files
3. Add PostgreSQL for persistence (future)
4. Configure CORS for production domain

## Development

### Run Tests

```bash
pytest physics_engine/ -v --cov=physics_engine
```

### Code Style

This project follows PEP 8 guidelines. Use:
```bash
pip install black flake8
black .
flake8 .
```

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify all dependencies are installed
- Check Python version (3.10+ required)

### STL upload fails
- Verify file is valid STL format (binary or ASCII)
- Check file size < 100MB
- Ensure triangle count < 1,000,000

### Simulation errors
- Check mesh quality (use validation endpoint)
- Verify material and scale mode are valid
- Review error logs in console

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

Educational use - AeroClass Project

## Documentation

- [Technical Analysis](docs/TECH.md) - Detailed technical documentation
- [Specification](docs/SPEC_REVISED.md) - Complete requirements specification
- [Error Log](docs/ERRORS.md) - Development error tracking

## Support

For issues and questions, please open an issue on GitHub.
