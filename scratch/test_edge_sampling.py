import numpy as np
from stl import mesh
import os

def run_simulation():
    filepath = "stl_samples/Part Studio 1.stl"
    m = mesh.Mesh.from_file(filepath)
    # Get the original triangles
    triangles = m.vectors.copy()
    
    # 1. Rotate X on all vertices in triangles
    t1 = triangles.copy()
    triangles[:, :, 1] = t1[:, :, 2]
    triangles[:, :, 2] = -t1[:, :, 1]
    
    # 2. Auto-Laydown
    # Find raw size
    all_v = triangles.reshape(-1, 3)
    min_c = all_v.min(axis=0)
    max_c = all_v.max(axis=0)
    raw_dims = max_c - min_c
    
    # Rotate Y (since rawSize.z is largest)
    t2 = triangles.copy()
    triangles[:, :, 0] = t2[:, :, 2]
    triangles[:, :, 2] = -t2[:, :, 0]
    
    # 3. Center
    all_v = triangles.reshape(-1, 3)
    min_c = all_v.min(axis=0)
    max_c = all_v.max(axis=0)
    center = (min_c + max_c) / 2.0
    triangles -= center
    
    # 4. Scale to maxDim = 4.0
    all_v = triangles.reshape(-1, 3)
    min_c = all_v.min(axis=0)
    max_c = all_v.max(axis=0)
    dims = max_c - min_c
    max_dim = np.max(dims)
    scale_factor = 4.0 / max_dim
    triangles *= scale_factor
    
    # Recompute bounds
    all_v = triangles.reshape(-1, 3)
    min_coords = all_v.min(axis=0)
    max_coords = all_v.max(axis=0)
    
    N = 200
    xLo = min_coords[0]
    xHi = max_coords[0]
    dxP = (xHi - xLo) / N
    
    roofArr = np.full(N, -np.inf)
    bellyArr = np.full(N, np.inf)
    sideArr = np.zeros(N)
    
    def hit(vx, vy, vz):
        si = int(np.floor((vx - xLo) / dxP))
        if si < 0 or si >= N:
            return
        if vy > roofArr[si]:
            roofArr[si] = vy
        if vy < bellyArr[si]:
            bellyArr[si] = vy
        if abs(vz) > sideArr[si]:
            sideArr[si] = abs(vz)
            
    # Sample both vertices AND edges!
    for tri in triangles:
        # 1. Sample vertices
        for v in tri:
            hit(v[0], v[1], v[2])
            
        # 2. Sample edges
        edges = [(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])]
        for A, B in edges:
            x_min = min(A[0], B[0])
            x_max = max(A[0], B[0])
            
            # Find slice indices spanned by this edge
            si_start = int(np.ceil((x_min - xLo) / dxP))
            si_end = int(np.floor((x_max - xLo) / dxP))
            
            for si in range(si_start, si_end + 1):
                if si < 0 or si >= N:
                    continue
                x_slice = xLo + si * dxP
                # Interpolate
                denom = B[0] - A[0]
                if abs(denom) > 1e-10:
                    t = (x_slice - A[0]) / denom
                    y_interp = A[1] + t * (B[1] - A[1])
                    z_interp = A[2] + t * (B[2] - A[2])
                    hit(x_slice, y_interp, z_interp)

    # Check for empty slices
    empty_slices = np.sum(~np.isfinite(roofArr))
    print("Empty slices count in roofArr after edge sampling:", empty_slices)
    
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
    
    print("Roof stats:")
    print("Max of roof:", np.max(roof))
    print("Min of roof:", np.min(roof))
    
    print("Values around center (index 95 to 105):")
    for idx in range(95, 106):
        print(f"Index {idx}: roofArr={roofArr[idx]:.4f}, roof={roof[idx]:.4f}")

run_simulation()
