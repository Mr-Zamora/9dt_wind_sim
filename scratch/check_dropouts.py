import numpy as np
from stl import mesh
import os

def run_simulation():
    filepath = "stl_samples/Part Studio 1.stl"
    m = mesh.Mesh.from_file(filepath)
    vertices = m.vectors.reshape(-1, 3).copy()
    
    # Rotate X
    v1 = vertices.copy()
    vertices[:, 1] = v1[:, 2]
    vertices[:, 2] = -v1[:, 1]
    
    # Rotate Y (since rawSize.z is largest)
    v2 = vertices.copy()
    vertices[:, 0] = v2[:, 2]
    vertices[:, 2] = -v2[:, 0]
    
    # Center
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    center = (min_coords + max_coords) / 2.0
    vertices -= center
    
    # Scale
    dims = max_coords - min_coords
    max_dim = np.max(dims)
    scale_factor = 4.0 / max_dim
    vertices *= scale_factor
    
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    
    N = 200
    xLo = min_coords[0]
    xHi = max_coords[0]
    dxP = (xHi - xLo) / N
    
    roofArr = np.full(N, -np.inf)
    
    for v in vertices:
        vx, vy, vz = v
        si = int(np.floor((vx - xLo) / dxP))
        if si < 0 or si >= N:
            continue
        if vy > roofArr[si]:
            roofArr[si] = vy
            
    # Print indices 90 to 120 of roofArr
    print("Raw roofArr values around center:")
    for i in range(90, 121):
        val = roofArr[i]
        print(f"  idx {i}: {val:.4f}")

run_simulation()
