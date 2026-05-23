import numpy as np
from stl import mesh
import os

filepath = "stl_samples/Part Studio 1.stl"
if os.path.exists(filepath):
    m = mesh.Mesh.from_file(filepath)
    vertices = m.vectors.reshape(-1, 3)
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    dims = max_coords - min_coords
    print("Part Studio 1.stl Stats:")
    print("Vertices count:", len(vertices))
    print("Min coords:", min_coords)
    print("Max coords:", max_coords)
    print("Dimensions:", dims)
else:
    print(f"{filepath} does not exist.")
