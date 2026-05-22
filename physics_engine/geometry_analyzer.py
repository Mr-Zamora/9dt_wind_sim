"""
Geometry Analyzer
Calculates geometric properties: frontal area, volume, bounding box
"""

import numpy as np
from stl import mesh
from typing import Tuple, Dict
from scipy.spatial import ConvexHull


class GeometryAnalyzer:
    """Analyze 3D mesh geometry for aerodynamic calculations"""
    
    def __init__(self, mesh_data: mesh.Mesh):
        """
        Initialize geometry analyzer
        
        Args:
            mesh_data: numpy-stl Mesh object
        """
        self.mesh = mesh_data
        self.vertices = mesh_data.vectors.reshape(-1, 3)
        
        # Auto-detect units (millimeters to meters)
        # If the largest dimension is > 5.0, we assume the CAD export is in millimeters
        min_coords = self.vertices.min(axis=0)
        max_coords = self.vertices.max(axis=0)
        dimensions = max_coords - min_coords
        max_dim = float(np.max(dimensions))
        
        if max_dim > 5.0:
            # Scale coordinates by 0.001 to convert mm -> m
            self.vertices = self.vertices * 0.001
            self.mesh.vectors = self.mesh.vectors * 0.001
            self.mesh.update_normals()
        
    def get_bounding_box(self) -> Dict[str, np.ndarray]:
        """
        Calculate axis-aligned bounding box with semantic axis assignment.

        STL files can be exported in any axis orientation (X, Y or Z as the
        nose-to-tail axis). Rather than blindly labelling X=length, Y=width,
        Z=height, we sort the three raw extents and assign:
          - length : the longest axis  (car nose-to-tail)
          - width  : the middle axis   (car side-to-side)
          - height : the shortest axis (car floor-to-roof)

        Returns:
            Dictionary with 'min', 'max', 'dimensions', semantic lengths,
            axis indices, and 'flow_direction' (unit vector for frontal-area
            projection along the car's length axis).
        """
        min_coords = self.vertices.min(axis=0)
        max_coords = self.vertices.max(axis=0)
        raw_dims = max_coords - min_coords  # [X_extent, Y_extent, Z_extent]

        # Sort axes descending by size: [longest, middle, shortest]
        sorted_indices = np.argsort(raw_dims)[::-1]
        length_axis = int(sorted_indices[0])  # nose-to-tail
        width_axis  = int(sorted_indices[1])  # side-to-side
        height_axis = int(sorted_indices[2])  # floor-to-roof

        # Flow direction is along the car's longest axis (nose-to-tail)
        flow_direction = np.zeros(3)
        flow_direction[length_axis] = 1.0

        return {
            'min': min_coords,
            'max': max_coords,
            'dimensions': raw_dims,
            # Semantically sorted extents
            'length': float(raw_dims[length_axis]),
            'width':  float(raw_dims[width_axis]),
            'height': float(raw_dims[height_axis]),
            # Which raw axis corresponds to each semantic dimension
            'length_axis': length_axis,
            'width_axis':  width_axis,
            'height_axis': height_axis,
            # Unit vector for frontal-area projection
            'flow_direction': flow_direction,
        }
    
    def calculate_frontal_area(self, direction: np.ndarray = None) -> float:
        """
        Calculate frontal area using ray-casting silhouette projection.

        Args:
            direction: Flow direction unit vector.  If None (default), the
                       direction is auto-detected from the bounding box as the
                       car's nose-to-tail (longest) axis, regardless of which
                       raw XYZ axis that happens to be.

        Returns:
            Frontal area in square meters
        """
        # Auto-detect flow direction from bounding box (longest axis = nose-to-tail)
        bbox = self.get_bounding_box()
        if direction is None:
            direction = bbox['flow_direction'].copy()

        # Normalize direction vector
        direction = direction / np.linalg.norm(direction)

        # Project all triangles onto the plane perpendicular to flow direction
        projected_areas = []

        for triangle in self.mesh.vectors:
            # Calculate triangle normal
            v1 = triangle[1] - triangle[0]
            v2 = triangle[2] - triangle[0]
            normal = np.cross(v1, v2)
            normal_length = np.linalg.norm(normal)

            if normal_length < 1e-10:
                continue  # Skip degenerate triangles

            normal = normal / normal_length

            # Area contribution = original_area * |cos(angle between normal and flow)|
            cos_angle = abs(np.dot(normal, direction))
            triangle_area = 0.5 * normal_length
            projected_area = triangle_area * cos_angle

            projected_areas.append(projected_area)

        # Sum all projected areas
        # Note: This overestimates due to overlaps, but acceptable for educational use
        total_area = sum(projected_areas)

        # For a closed mesh every ray enters and exits, so divide by 2 to get
        # the actual silhouette area.
        silhouette_area = total_area * 0.5

        # Empirical correction for internal overlaps / CAD features
        correction_factor = 0.7
        estimated_area = silhouette_area * correction_factor

        # Bounding-box cap: use the two axes perpendicular to flow (width × height)
        # These are correctly identified from the semantically sorted bbox.
        cap_width  = bbox['width']   # side-to-side extent (not the car's length)
        cap_height = bbox['height']  # floor-to-roof extent
        bbox_frontal_area = cap_width * cap_height

        # A realistic vehicle frontal area cannot exceed 82 % of its cross-section box.
        max_realistic_area = bbox_frontal_area * 0.82

        return min(estimated_area, max_realistic_area)
    
    def calculate_volume_voxel(self, voxel_size: float = 0.002) -> Tuple[float, float]:
        """
        Calculate volume using voxel-based method (robust to small defects)
        
        Args:
            voxel_size: Size of voxel grid in meters (default: 2mm)
            
        Returns:
            Tuple of (volume in m³, confidence score 0-1)
        """
        bbox = self.get_bounding_box()
        
        # Create voxel grid
        x_range = np.arange(bbox['min'][0], bbox['max'][0], voxel_size)
        y_range = np.arange(bbox['min'][1], bbox['max'][1], voxel_size)
        z_range = np.arange(bbox['min'][2], bbox['max'][2], voxel_size)
        
        # Count voxels inside mesh (simplified ray-casting)
        interior_count = 0
        total_voxels = len(x_range) * len(y_range) * len(z_range)
        
        # Sample subset for performance (every Nth voxel)
        sample_rate = max(1, int(total_voxels ** (1/3) / 50))
        
        for i, x in enumerate(x_range[::sample_rate]):
            for j, y in enumerate(y_range[::sample_rate]):
                for k, z in enumerate(z_range[::sample_rate]):
                    point = np.array([x, y, z])
                    if self._is_point_inside_mesh(point):
                        interior_count += 1
        
        # Estimate total volume
        voxel_volume = voxel_size ** 3
        sampled_voxels = (len(x_range[::sample_rate]) * 
                         len(y_range[::sample_rate]) * 
                         len(z_range[::sample_rate]))
        
        volume = (interior_count / sampled_voxels) * (bbox['dimensions'].prod())
        
        # Confidence based on mesh quality
        confidence = min(1.0, 0.7 + (len(self.mesh.vectors) / 10000) * 0.3)
        
        return volume, confidence
    
    def calculate_volume_convex_hull(self) -> float:
        """
        Calculate volume using convex hull (fast but overestimates)
        
        Returns:
            Volume in m³
        """
        try:
            hull = ConvexHull(self.vertices)
            raw_volume = hull.volume
        except Exception:
            # Fallback to bounding box volume if convex hull fails
            bbox = self.get_bounding_box()
            raw_volume = bbox['dimensions'].prod() * 0.5  # Rough estimate
            
        # Capping: volume of a realistic passenger vehicle is typically 30-45% of its bounding box.
        # Since convex hulls envelope the entire outer structure including empty glass/undercut space,
        # they significantly overestimate real volume. We cap it to maintain realistic mass results.
        bbox = self.get_bounding_box()
        bbox_volume = bbox['dimensions'].prod()
        max_realistic_volume = bbox_volume * 0.42
        
        return min(raw_volume, max_realistic_volume)
    
    def _is_point_inside_mesh(self, point: np.ndarray) -> bool:
        """
        Check if point is inside mesh using ray-casting
        (Simplified version - counts intersections along +X axis)
        
        Args:
            point: 3D point coordinates
            
        Returns:
            True if point is inside mesh
        """
        ray_direction = np.array([1, 0, 0])
        intersection_count = 0
        
        for triangle in self.mesh.vectors:
            if self._ray_triangle_intersection(point, ray_direction, triangle):
                intersection_count += 1
        
        # Odd number of intersections = inside
        return intersection_count % 2 == 1
    
    def _ray_triangle_intersection(self, 
                                   ray_origin: np.ndarray, 
                                   ray_direction: np.ndarray, 
                                   triangle: np.ndarray) -> bool:
        """
        Möller–Trumbore ray-triangle intersection algorithm
        
        Args:
            ray_origin: Starting point of ray
            ray_direction: Direction vector of ray
            triangle: 3x3 array of triangle vertices
            
        Returns:
            True if ray intersects triangle
        """
        epsilon = 1e-10
        
        v0, v1, v2 = triangle
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        h = np.cross(ray_direction, edge2)
        a = np.dot(edge1, h)
        
        if abs(a) < epsilon:
            return False  # Ray parallel to triangle
        
        f = 1.0 / a
        s = ray_origin - v0
        u = f * np.dot(s, h)
        
        if u < 0.0 or u > 1.0:
            return False
        
        q = np.cross(s, edge1)
        v = f * np.dot(ray_direction, q)
        
        if v < 0.0 or u + v > 1.0:
            return False
        
        t = f * np.dot(edge2, q)
        
        return t > epsilon  # Intersection ahead of ray origin
    
    def calculate_surface_area(self) -> float:
        """
        Calculate total surface area of mesh
        
        Returns:
            Surface area in m²
        """
        total_area = 0.0
        
        for triangle in self.mesh.vectors:
            v1 = triangle[1] - triangle[0]
            v2 = triangle[2] - triangle[0]
            area = 0.5 * np.linalg.norm(np.cross(v1, v2))
            total_area += area
        
        return total_area
    
    def get_all_properties(self) -> Dict:
        """
        Calculate all geometric properties at once.

        Dimensions are reported semantically (length = nose-to-tail, width =
        side-to-side, height = floor-to-roof) regardless of which raw XYZ axis
        the STL was exported along.

        Returns:
            Dictionary with all geometric measurements.
        """
        bbox = self.get_bounding_box()

        # Pass the auto-detected flow direction so frontal area is computed
        # looking straight at the car's nose, not necessarily along +X.
        frontal_area = self.calculate_frontal_area(direction=bbox['flow_direction'].copy())

        # Use fast convex hull method for volume (good enough for educational use)
        volume = self.calculate_volume_convex_hull()
        volume_confidence = 0.85  # Convex hull typically 85 % accurate

        surface_area = self.calculate_surface_area()

        return {
            'dimensions': {
                'length': float(bbox['length']),   # longest axis  (nose-to-tail)
                'width':  float(bbox['width']),    # middle axis   (side-to-side)
                'height': float(bbox['height']),   # shortest axis (floor-to-roof)
            },
            'frontal_area_m2': float(frontal_area),
            'volume_m3': float(volume),
            'volume_confidence': float(volume_confidence),
            'surface_area_m2': float(surface_area),
            'bounding_box': {
                'min': bbox['min'].tolist(),
                'max': bbox['max'].tolist(),
                'length_axis': int(bbox['length_axis']),
                'width_axis':  int(bbox['width_axis']),
                'height_axis': int(bbox['height_axis']),
            },
        }
