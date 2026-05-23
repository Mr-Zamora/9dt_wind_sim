import numpy as np
from stl import mesh
import os

def run_simulation():
    filepath = "stl_samples/Part Studio 1.stl"
    if not os.path.exists(filepath):
        print("File not found")
        return
        
    m = mesh.Mesh.from_file(filepath)
    # Reshape vectors to get vertices
    vertices = m.vectors.reshape(-1, 3).copy()
    
    # 1. Rotate X (-pi/2)
    # y' = z, z' = -y
    v1 = vertices.copy()
    vertices[:, 1] = v1[:, 2]
    vertices[:, 2] = -v1[:, 1]
    
    # 2. Auto-Laydown
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    raw_dims = max_coords - min_coords
    
    # Since rawSize.z is largest (137.04), we rotateY(pi/2)
    # x' = z, z' = -x
    v2 = vertices.copy()
    vertices[:, 0] = v2[:, 2]
    vertices[:, 2] = -v2[:, 0]
    
    # 3. Center
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    center = (min_coords + max_coords) / 2.0
    vertices -= center
    
    # 4. Scale to maxDim = 4.0
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    dims = max_coords - min_coords
    max_dim = np.max(dims)
    scale_factor = 4.0 / max_dim
    vertices *= scale_factor
    
    # Recompute bounds
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    dims = max_coords - min_coords
    print("Centered and scaled stats:")
    print("Min:", min_coords)
    print("Max:", max_coords)
    print("Dims:", dims)
    
    # Run profiling logic
    N = 200
    xLo = min_coords[0]
    xHi = max_coords[0]
    dxP = (xHi - xLo) / N
    
    roofArr = np.full(N, -np.inf)
    bellyArr = np.full(N, np.inf)
    sideArr = np.zeros(N)
    
    for v in vertices:
        vx, vy, vz = v
        si = int(np.floor((vx - xLo) / dxP))
        if si < 0 or si >= N:
            continue
        if vy > roofArr[si]:
            roofArr[si] = vy
        if vy < bellyArr[si]:
            bellyArr[si] = vy
        if abs(vz) > sideArr[si]:
            sideArr[si] = abs(vz)
            
    # Check for empty slices
    empty_slices = np.sum(~np.isfinite(roofArr))
    print("Empty slices count in roofArr:", empty_slices)
    
    # Fill empty slices
    def fill_array(arr, fallback_val):
        valid_indices = [i for i, val in enumerate(arr) if np.isfinite(val)]
        if not valid_indices:
            arr.fill(fallback_val)
            return
            
        first_idx = valid_indices[0]
        first_val = arr[first_idx]
        arr[:first_idx] = first_val
        
        last_idx = valid_indices[-1]
        last_val = arr[last_idx]
        arr[last_idx+1:] = last_val
        
        for k in range(len(valid_indices) - 1):
            left = valid_indices[k]
            right = valid_indices[k+1]
            left_val = arr[left]
            right_val = arr[right]
            for i in range(left + 1, right):
                t = (i - left) / (right - left)
                arr[i] = left_val + (right_val - left_val) * t
                
    fill_array(roofArr, 0.0)
    fill_array(bellyArr, 0.0)
    
    # Interpolate sideArr gaps
    valid_side = [i for i, val in enumerate(sideArr) if val > 0]
    if valid_side:
        first_val = sideArr[valid_side[0]]
        sideArr[:valid_side[0]] = first_val
        last_val = sideArr[valid_side[-1]]
        sideArr[valid_side[-1]+1:] = last_val
        for k in range(len(valid_side) - 1):
            left = valid_side[k]
            right = valid_side[k+1]
            left_val = sideArr[left]
            right_val = sideArr[right]
            for i in range(left + 1, right):
                t = (i - left) / (right - left)
                sideArr[i] = left_val + (right_val - left_val) * t
                
    # Smooth
    def smooth(arr, w=6):
        out = arr.copy()
        n = len(arr)
        for i in range(n):
            currentW = min(w, i, n - 1 - i)
            s = 0
            for k in range(-currentW, currentW + 1):
                s += arr[i + k]
            out[i] = s / (2 * currentW + 1)
        return out
        
    roof = smooth(roofArr, 6)
    belly = smooth(bellyArr, 6)
    side = smooth(sideArr, 7)
    
    print("Roof stats:")
    print("Max of roof:", np.max(roof))
    print("Min of roof:", np.min(roof))
    print("Side stats:")
    print("Max of side:", np.max(side))
    
    # Check values at center slices (around index 100)
    print("Values around center (index 95 to 105):")
    for idx in range(95, 106):
        print(f"Index {idx}: roofArr={roofArr[idx]:.4f}, roof={roof[idx]:.4f}, belly={belly[idx]:.4f}, side={side[idx]:.4f}")

run_simulation()
