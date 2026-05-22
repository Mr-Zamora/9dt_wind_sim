# Test STL Samples

This folder contains sample STL files for testing the physics engine.

## How to Add Test Files

1. Export a vehicle design from Onshape as STL
2. Place the file in this directory
3. Run: `python demo.py test_samples/your_file.stl`

## Expected File Properties

- **Format**: Binary or ASCII STL
- **Size**: < 100 MB
- **Triangles**: < 1,000,000
- **Scale**: Meters (not millimeters)

## Sample Files Needed

- Simple box car (for validation)
- Streamlined vehicle (low Cd)
- Blunt vehicle (high Cd)
- Student CO2 dragster designs
