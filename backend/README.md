# AeroClass FastAPI Backend

REST API for the AeroClass aerodynamics simulation platform.

## Features

- **STL Upload**: Upload and validate vehicle designs
- **Aerodynamic Simulation**: Run quick preview or detailed analysis
- **Material Comparison**: Compare performance across different materials
- **Scale Analysis**: Compare miniature vs full-scale performance
- **Auto-generated API docs**: Swagger UI and ReDoc

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Running the Server

### Development Mode
```bash
python main.py
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server will start at: `http://localhost:8000`

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## API Endpoints

### Health Check
- `GET /api/health` - Server health status
- `GET /api/ping` - Simple ping test

### Design Management
- `POST /api/designs/upload` - Upload STL file
- `GET /api/designs/{design_id}` - Get design info
- `DELETE /api/designs/{design_id}` - Delete design

### Simulations
- `POST /api/simulations/run` - Run simulation
- `GET /api/simulations/{design_id}/materials` - Material comparison
- `GET /api/simulations/{design_id}/scales` - Scale comparison

## Example Usage

### 1. Upload Design
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
    "engine_power_hp": 150
  }'
```

Response:
```json
{
  "simulation_id": "xyz789...",
  "design_id": "abc123...",
  "status": "completed",
  "estimated_cd": 0.29,
  "top_speed_kmh": 237.5,
  "acceleration_0_100_sec": 5.3,
  "vehicle_mass_kg": 1254,
  ...
}
```

### 3. Compare Materials
```bash
curl "http://localhost:8000/api/simulations/abc123.../materials?engine_power_hp=150"
```

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── routers/               # API route handlers
│   ├── health.py          # Health check endpoints
│   ├── designs.py         # Design management
│   └── simulations.py     # Simulation endpoints
├── models/                # Pydantic schemas
│   └── schemas.py         # Request/response models
├── services/              # Business logic
│   └── physics_service.py # Physics engine wrapper
└── uploads/               # STL file storage (auto-created)
```

## Configuration

Environment variables (optional):
- `API_HOST` - Server host (default: 0.0.0.0)
- `API_PORT` - Server port (default: 8000)
- `UPLOAD_DIR` - Upload directory (default: ./uploads)
- `MAX_FILE_SIZE_MB` - Max upload size (default: 100)

## Development

### Run with auto-reload
```bash
uvicorn main:app --reload
```

### Run tests (future)
```bash
pytest tests/ -v
```

## CORS Configuration

Currently allows all origins for development. In production, update `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    ...
)
```

## Next Steps

- [ ] Add database integration (PostgreSQL)
- [ ] Implement user authentication
- [ ] Add async task queue (Celery + Redis)
- [ ] Add WebSocket for real-time progress
- [ ] Implement caching layer
- [ ] Add rate limiting
- [ ] Deploy to cloud (AWS/Azure/GCP)

## License

Educational use - AeroClass Project
