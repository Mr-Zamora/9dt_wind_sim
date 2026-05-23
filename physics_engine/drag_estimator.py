"""
Drag Coefficient Estimator
Computes Cd via surface pressure integration (Modified Newtonian method).

Every triangle on the STL mesh contributes to drag based on how directly
it faces the airflow.  A slanted windshield, tapered nose or boat-tailed
rear all reduce Cd measurably, so students can iterate their design and
see real aerodynamic improvement.

Method
------
For each mesh triangle with outward-facing unit normal n and flow direction f:

  incidence  =  max( -dot(n, f), 0 )        # 0 = parallel, 1 = head-on
  Cp_wind    ≈  incidence²                   # Newtonian pressure coefficient
  dCd_wind   =  Cp_wind × dA / A_ref

  Leeward faces (incidence = 0) contribute a small constant wake suction.

Calibration
-----------
A flat plate perpendicular to the flow gives Σ(cos²θ × dA) = A_frontal,
so P_raw = 1.0.  Scaling by PRESSURE_CALIBRATION = 0.45 maps:
  flat plate  → Cd ≈ 0.47  (real: ~1.1 for high-AR plate, ~0.45 for cars)
  box car     → Cd ≈ 0.45–0.50
  sedan       → Cd ≈ 0.28–0.35
  streamlined → Cd ≈ 0.18–0.26

Absolute values are approximate; changes are directionally accurate.
"""

import numpy as np
from typing import Dict, Tuple
from stl import mesh


class DragEstimator:
    """Estimate drag coefficient via surface pressure integration."""

    RHO_AIR = 1.225            # kg/m³  — sea level 15 °C
    PRESSURE_CALIBRATION = 0.38 # maps raw P=1 (flat plate) → Cd ≈ 0.38; typical car Cd 0.30–0.55
    CD_SKIN_FRICTION = 0.025    # viscous / skin-friction contribution
    CD_WAKE_FRACTION = 0.05     # leeward wake suction (fraction of leeward area ratio)

    # ------------------------------------------------------------------ #
    #  Construction & axis detection
    # ------------------------------------------------------------------ #

    def __init__(self, mesh_data: mesh.Mesh, frontal_area: float):
        """
        Parameters
        ----------
        mesh_data    : numpy-stl Mesh object
        frontal_area : projected frontal area in m² (from GeometryAnalyzer)
        """
        self.mesh = mesh_data
        self.frontal_area = max(frontal_area, 1e-9)
        self.features: Dict = {}

        vertices = mesh_data.vectors.reshape(-1, 3)

        # ── Detect semantic axes (same approach as GeometryAnalyzer) ──────
        min_c    = vertices.min(axis=0)
        max_c    = vertices.max(axis=0)
        raw_dims = max_c - min_c

        sorted_idx         = np.argsort(raw_dims)[::-1]   # largest first
        self._la           = int(sorted_idx[0])  # length axis (nose-to-tail)
        self._wa           = int(sorted_idx[1])  # width  axis (side-to-side)
        self._ha           = int(sorted_idx[2])  # height axis (floor-to-roof)
        self._min_c        = min_c
        self._max_c        = max_c
        self._raw_dims     = raw_dims

        # ── Detect which end is the nose ──────────────────────────────────
        self._flow_dir     = self._detect_nose_direction(vertices)

        # Mesh centroid — used to orient triangle normals outward
        self._centroid     = vertices.mean(axis=0)

    # ------------------------------------------------------------------ #
    #  Nose detection
    # ------------------------------------------------------------------ #

    def _detect_nose_direction(self, vertices: np.ndarray) -> np.ndarray:
        """
        Return a unit flow-direction vector pointing FROM the nose end.

        Heuristic: the end with the smaller cross-sectional bounding box
        is more likely the nose (cars taper at the front).
        """
        la, wa, ha = self._la, self._wa, self._ha
        L  = self._raw_dims[la]
        lo = self._min_c[la]
        hi = self._max_c[la]

        def cross_section(mask: np.ndarray) -> float:
            v = vertices[mask]
            if len(v) < 3:
                return float('inf')
            w = float(v[:, wa].max() - v[:, wa].min())
            h = float(v[:, ha].max() - v[:, ha].min())
            return w * h

        front_cs = cross_section(vertices[:, la] < lo + L * 0.15)
        rear_cs  = cross_section(vertices[:, la] > hi - L * 0.15)

        flow = np.zeros(3)
        if front_cs <= rear_cs:
            # Narrower end is at the min-length side → flow comes from -la direction
            flow[la] = -1.0
        else:
            # Narrower end is at the max-length side → flow comes from +la direction
            flow[la] = 1.0
        return flow

    # ------------------------------------------------------------------ #
    #  Normal computation
    # ------------------------------------------------------------------ #

    def _outward_normal(self, triangle: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Compute the outward-pointing unit normal and area of a triangle.

        Uses the centroid check: if the computed normal points toward the
        mesh centroid, it is inward → flip it.
        """
        v1 = triangle[1] - triangle[0]
        v2 = triangle[2] - triangle[0]
        cross = np.cross(v1, v2)
        norm_len = np.linalg.norm(cross)

        if norm_len < 1e-12:
            return np.array([0.0, 0.0, 1.0]), 0.0

        area   = 0.5 * norm_len
        normal = cross / norm_len          # unit normal (orientation unknown)

        # Ensure normal points away from centroid (outward)
        face_centre = triangle.mean(axis=0)
        out_vec     = face_centre - self._centroid
        dot_check   = np.dot(normal, out_vec)
        if abs(dot_check) > 1e-9 and dot_check < 0:
            normal = -normal

        return normal, area

    # ------------------------------------------------------------------ #
    #  Core estimator — pressure integration
    # ------------------------------------------------------------------ #

    def estimate_cd_pressure_integration(self) -> Tuple[float, Dict]:
        """
        Compute Cd by integrating pressure over every triangle.

        Returns
        -------
        cd        : float — estimated drag coefficient
        breakdown : dict  — detailed per-component breakdown
        """
        flow = self._flow_dir    # unit vector in flow direction

        windward_drag_area = 0.0   # Σ cos²θ × area  for windward faces
        leeward_area_total = 0.0   # total area of leeward (wake) faces
        total_area         = 0.0

        for triangle in self.mesh.vectors:
            normal, area = self._outward_normal(triangle)
            if area < 1e-12:
                continue
            total_area += area

            # dot(normal, flow):
            #   negative → normal opposes flow → WINDWARD (pressure) face
            #   positive → normal aligns with flow → LEEWARD  (wake)   face
            cos_theta = float(np.dot(normal, flow))

            if cos_theta < 0:
                incidence           = -cos_theta              # 0 (grazing) … 1 (head-on)
                windward_drag_area += area * (incidence ** 2) # Newtonian Cp ∝ cos²θ
            else:
                leeward_area_total += area

        if self.frontal_area < 1e-12 or total_area < 1e-12:
            return 0.35, {}

        # Pressure drag (dominant)
        pressure_cd = (windward_drag_area * self.PRESSURE_CALIBRATION) / self.frontal_area

        # Wake / base drag (suction behind the vehicle)
        leeward_fraction = leeward_area_total / total_area
        wake_cd = leeward_fraction * self.CD_WAKE_FRACTION

        cd = float(np.clip(pressure_cd + wake_cd + self.CD_SKIN_FRICTION, 0.10, 1.20))

        breakdown = {
            'pressure_cd':         pressure_cd,
            'wake_cd':             wake_cd,
            'friction_cd':         self.CD_SKIN_FRICTION,
            'windward_drag_area':  windward_drag_area,
            'leeward_area_total':  leeward_area_total,
            'total_mesh_area':     total_area,
            'leeward_fraction':    leeward_fraction,
            'flow_direction':      flow.tolist(),
        }
        return cd, breakdown

    # ------------------------------------------------------------------ #
    #  Public helpers
    # ------------------------------------------------------------------ #

    def estimate_cd_quick(self) -> float:
        """Main public interface — returns estimated Cd."""
        cd, _ = self.estimate_cd_pressure_integration()
        return cd

    def calculate_drag_force(self, velocity: float, cd: float = None) -> float:
        """Drag force in Newtons at given velocity (m/s)."""
        if cd is None:
            cd = self.estimate_cd_quick()
        return 0.5 * self.RHO_AIR * (velocity ** 2) * cd * self.frontal_area

    def get_detailed_analysis(self) -> Dict:
        """
        Full analysis returned to the router.
        Backward-compatible: returns same top-level keys as before.
        """
        if not self.features:
            self.analyze_features()

        cd, breakdown = self.estimate_cd_pressure_integration()

        return {
            'estimated_cd': cd,
            'factors': {
                'pressure_cd':    breakdown.get('pressure_cd', 0.0),
                'wake_cd':        breakdown.get('wake_cd', 0.0),
                'friction_cd':    breakdown.get('friction_cd', 0.0),
                'flow_direction': breakdown.get('flow_direction', []),
            },
            'features': self.features,
            'drag_breakdown': {
                # approximate percentages for UI display
                'pressure_drag_pct': round(breakdown.get('pressure_cd', 0) / max(cd, 1e-6) * 100, 1),
                'skin_friction_pct': round(breakdown.get('friction_cd', 0) / max(cd, 1e-6) * 100, 1),
                'wake_drag_pct':     round(breakdown.get('wake_cd',     0) / max(cd, 1e-6) * 100, 1),
            },
        }

    # ------------------------------------------------------------------ #
    #  Geometric feature analysis  (informational / breakdown display)
    # ------------------------------------------------------------------ #

    def analyze_features(self) -> Dict:
        """
        Extract secondary geometric features for the breakdown panel.
        Uses the semantically correct axes (not hardcoded X = length).
        """
        vertices = self.mesh.vectors.reshape(-1, 3)
        la, wa, ha = self._la, self._wa, self._ha

        length = float(self._raw_dims[la])
        width  = float(self._raw_dims[wa])
        height = float(self._raw_dims[ha])

        # Determine nose / rear positions along the length axis
        if self._flow_dir[la] < 0:
            nose_end = float(self._min_c[la])   # flow from min end → nose at min
            rear_end = float(self._max_c[la])
        else:
            nose_end = float(self._max_c[la])   # flow from max end → nose at max
            rear_end = float(self._min_c[la])

        self.features = {
            'length':             length,
            'width':              width,
            'height':             height,
            'aspect_ratio':       length / max(width,  1e-6),
            'fineness_ratio':     length / max(float(np.sqrt(width * height)), 1e-6),
            'nose_radius':        self._nose_radius(vertices, nose_end, la, length),
            'rear_taper_angle':   self._rear_taper(vertices, rear_end, la, length),
            'surface_smoothness': self._surface_smoothness(),
            'underbody_flatness': self._underbody_flatness(vertices, ha, height),
            'flow_direction':     self._flow_dir.tolist(),
        }
        return self.features

    # ── Private feature helpers ──────────────────────────────────────── #

    def _nose_radius(self, vertices: np.ndarray,
                     nose_pos: float, la: int, length: float) -> float:
        """Estimate nose bluntness from vertex spread in the front 10 %."""
        wa, ha = self._wa, self._ha
        if self._flow_dir[la] < 0:
            mask = vertices[:, la] < nose_pos + length * 0.10
        else:
            mask = vertices[:, la] > nose_pos - length * 0.10
        v = vertices[mask]
        if len(v) < 3:
            return 0.1
        y_r = float(v[:, wa].max() - v[:, wa].min())
        z_r = float(v[:, ha].max() - v[:, ha].min())
        return float(np.clip((y_r + z_r) / 4.0, 0.01, 0.5))

    def _rear_taper(self, vertices: np.ndarray,
                    rear_pos: float, la: int, length: float) -> float:
        """Estimate boat-tail taper angle from cross-section change in rear 30 %."""
        wa, ha = self._wa, self._ha
        if self._flow_dir[la] < 0:
            # rear is at max end
            thr = rear_pos - length * 0.30
            rear_v = vertices[vertices[:, la] > thr]
            xs = np.linspace(thr, rear_pos, 5)
        else:
            # rear is at min end
            thr = rear_pos + length * 0.30
            rear_v = vertices[vertices[:, la] < thr]
            xs = np.linspace(rear_pos, thr, 5)

        if len(rear_v) < 10:
            return 0.0

        areas = []
        for x in xs:
            sv = rear_v[np.abs(rear_v[:, la] - x) < 0.05]
            if len(sv) > 0:
                w = float(sv[:, wa].max() - sv[:, wa].min())
                h = float(sv[:, ha].max() - sv[:, ha].min())
                areas.append(w * h)

        if len(areas) < 2:
            return 0.0

        ratio = areas[-1] / max(areas[0], 1e-9)
        if ratio < 0.7:
            return 15.0
        elif ratio < 0.9:
            return 5.0
        return 0.0

    def _surface_smoothness(self) -> float:
        """
        Smoothness score (0–1).  Based on triangle-size uniformity:
        a high-poly smooth model has uniform small triangles; a faceted
        low-poly model has high variation.
        """
        areas = []
        for tri in self.mesh.vectors:
            v1 = tri[1] - tri[0]
            v2 = tri[2] - tri[0]
            areas.append(0.5 * float(np.linalg.norm(np.cross(v1, v2))))
        if not areas or float(np.mean(areas)) < 1e-12:
            return 0.5
        cv = float(np.std(areas)) / float(np.mean(areas))
        return float(1.0 / (1.0 + cv))

    def _underbody_flatness(self, vertices: np.ndarray,
                            ha: int, height: float) -> float:
        """Flatness of the underbody (higher = flatter = better ground effect)."""
        z_thr = float(vertices[:, ha].min()) + height * 0.20
        bot   = vertices[vertices[:, ha] < z_thr]
        if len(bot) < 10:
            return 0.5
        z_std = float(np.std(bot[:, ha]))
        return float(1.0 - min(z_std / max(height * 0.1, 1e-6), 1.0))
