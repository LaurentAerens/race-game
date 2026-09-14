import json
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.interpolate import CubicSpline


class Circuit:
    """
    Continuous 2D Race Circuit represented by smooth periodic cubic splines.
    Supports variable per-section track width, DRS zones, interactive pit lane editor,
    and free 3-compound weekend tyre allocations.
    """

    def __init__(self, name: str = "Custom Circuit", width: float = 14.0):
        self.name = name
        self.width = width
        self.control_points: List[Tuple[float, float]] = []
        self.node_widths: List[float] = []
        self.is_closed: bool = True

        # Spline evaluations
        self.length: float = 0.0
        self.sample_step: float = 2.0  # Sample resolution in meters
        self.spline_x = None
        self.spline_y = None
        self.spline_w = None

        # Precomputed tables for ultra-fast lookup
        self.s_samples: np.ndarray = np.array([])
        self.points: np.ndarray = np.empty((0, 2))
        self.tangents: np.ndarray = np.empty((0, 2))
        self.normals: np.ndarray = np.empty((0, 2))
        self.curvatures: np.ndarray = np.array([])
        self.signed_curvatures: np.ndarray = np.array([])
        self.headings: np.ndarray = np.array([])
        self.widths_sample: np.ndarray = np.array([])

        # Track features
        self.sectors: List[float] = [0.33, 0.66, 1.0]  # Proportions of track length
        self.drs_zones: List[Dict] = []  # [{name, start_s, end_s, node_a, node_b}]
        self.node_s_distances: List[float] = []
        self.nominated_compounds: List[str] = ["HARD", "SOFT", "SUPERSOFT"]
        self.base_rain_chance: float = 0.20

        # Interactive Pit Lane Configuration
        self.pit_lane_enabled: bool = True
        self.pit_entry_node: Optional[int] = None
        self.pit_exit_node: Optional[int] = None
        self.pit_side: str = "INSIDE"  # "INSIDE" (-1.0) or "OUTSIDE" (+1.0)
        self.pit_offset_m: float = 14.0
        self.pit_box_s: float = 0.5  # Relative proportion along pit lane [0, 1]

        self.pit_entry_s: float = 0.0
        self.pit_exit_s: float = 0.0
        self.pit_control_points: List[Tuple[float, float]] = []
        self.pit_length: float = 0.0
        self.pit_points: np.ndarray = np.empty((0, 2))
        self.pit_tangents: np.ndarray = np.empty((0, 2))
        self.pit_s_samples: np.ndarray = np.array([])

    def set_control_points(self, points: List[Tuple[float, float]], widths: Optional[List[float]] = None):
        self.control_points = [(float(p[0]), float(p[1])) for p in points]
        if widths and len(widths) == len(points):
            self.node_widths = [float(w) for w in widths]
        else:
            self.node_widths = [float(self.width)] * len(points)
        self.build_circuit()

    def set_node_width(self, node_idx: int, width_m: float):
        """Sets the width for a specific corner/node."""
        if 0 <= node_idx < len(self.node_widths):
            self.node_widths[node_idx] = max(7.0, min(30.0, float(width_m)))
            self.build_circuit()

    def set_pit_lane_endpoints(self, entry_node: int, exit_node: int, side: str = "INSIDE", offset_m: float = 14.0):
        """Configures the pit lane endpoints and lateral side."""
        self.pit_entry_node = entry_node
        self.pit_exit_node = exit_node
        self.pit_side = side.upper()
        self.pit_offset_m = max(8.0, min(35.0, offset_m))
        self.build_circuit()

    def build_circuit(self):
        """Builds periodic cubic splines for coordinates, variable track width, and dynamic pit lane."""
        if len(self.control_points) < 3:
            return

        if len(self.node_widths) != len(self.control_points):
            self.node_widths = [float(self.width)] * len(self.control_points)

        pts = np.array(self.control_points, dtype=np.float64)
        widths_arr = np.array(self.node_widths, dtype=np.float64)

        if self.is_closed:
            pts_closed = np.vstack([pts, pts[0]])
            widths_closed = np.append(widths_arr, widths_arr[0])
        else:
            pts_closed = pts
            widths_closed = widths_arr

        # Compute chord lengths
        diffs = np.diff(pts_closed, axis=0)
        seg_lens = np.sqrt((diffs**2).sum(axis=1))
        seg_lens = np.maximum(seg_lens, 1e-4)
        cum_dist = np.insert(np.cumsum(seg_lens), 0, 0.0)
        self.length = float(cum_dist[-1])
        self.node_s_distances = [float(d) for d in cum_dist[:-1]]

        if self.length < 10.0:
            return

        bc = "periodic" if self.is_closed else "not-a-knot"

        self.spline_x = CubicSpline(cum_dist, pts_closed[:, 0], bc_type=bc)
        self.spline_y = CubicSpline(cum_dist, pts_closed[:, 1], bc_type=bc)
        self.spline_w = CubicSpline(cum_dist, widths_closed, bc_type=bc)

        # Lookup samples every ~2 meters
        num_samples = max(50, int(self.length / self.sample_step))
        self.s_samples = np.linspace(0, self.length, num_samples, endpoint=False)

        px = self.spline_x(self.s_samples)
        py = self.spline_y(self.s_samples)
        self.points = np.column_stack([px, py])

        # Smooth variable width profile
        w_eval = self.spline_w(self.s_samples)
        self.widths_sample = np.clip(w_eval, 7.0, 30.0)

        # Tangents and normals
        dx = self.spline_x(self.s_samples, 1)
        dy = self.spline_y(self.s_samples, 1)
        speed = np.maximum(np.sqrt(dx**2 + dy**2), 1e-6)
        tx = dx / speed
        ty = dy / speed
        self.tangents = np.column_stack([tx, ty])
        self.normals = np.column_stack([-ty, tx])
        self.headings = np.arctan2(ty, tx)

        # Curvature
        ddx = self.spline_x(self.s_samples, 2)
        ddy = self.spline_y(self.s_samples, 2)
        signed_k = (dx * ddy - dy * ddx) / (speed**3)
        self.signed_curvatures = signed_k
        self.curvatures = np.abs(signed_k)

        self.build_pit_lane()
        self.update_drs_zones()

    def update_drs_zones(self):
        """Synchronizes start_s and end_s of each DRS zone with its nominated node_a and node_b."""
        if not self.node_s_distances:
            return
        n = len(self.node_s_distances)
        for zone in self.drs_zones:
            node_a = zone.get("node_a")
            node_b = zone.get("node_b")
            if node_a is not None and node_b is not None and 0 <= node_a < n and 0 <= node_b < n:
                zone["start_s"] = float(self.node_s_distances[node_a])
                zone["end_s"] = float(self.node_s_distances[node_b])

    def build_pit_lane(self):
        """Constructs an attached, continuous pit lane spline between nominated entry and exit nodes."""
        if len(self.control_points) < 3 or not self.node_s_distances:
            return

        n_nodes = len(self.node_s_distances)
        if self.pit_entry_node is None:
            entry_idx = n_nodes - 1
        else:
            entry_idx = self.pit_entry_node % n_nodes

        if self.pit_exit_node is None:
            exit_idx = min(2, n_nodes - 1)
        else:
            exit_idx = self.pit_exit_node % n_nodes

        if entry_idx == exit_idx:
            exit_idx = (entry_idx + 1) % n_nodes

        self.pit_entry_node = entry_idx
        self.pit_exit_node = exit_idx

        entry_s = self.node_s_distances[entry_idx]
        exit_s = self.node_s_distances[exit_idx]
        self.pit_entry_s = entry_s
        self.pit_exit_s = exit_s

        side_sign = -1.0 if self.pit_side == "INSIDE" else 1.0

        # Compute span distance along track loop
        span_dist = (exit_s - entry_s) % self.length
        if span_dist < 40.0:
            span_dist += self.length

        # Anchor pit lane entry and exit seamlessly to the edge of the circuit asphalt
        entry_w = self.get_width(entry_s)
        exit_w = self.get_width(exit_s)

        p1 = self.get_position(entry_s, lateral_offset=side_sign * (entry_w * 0.45))
        p2 = self.get_position(
            (entry_s + span_dist * 0.18) % self.length, lateral_offset=side_sign * (entry_w * 0.5 + 4.0)
        )
        p3 = self.get_position(
            (entry_s + span_dist * 0.50) % self.length, lateral_offset=side_sign * (entry_w * 0.5 + self.pit_offset_m)
        )
        p4 = self.get_position(
            (entry_s + span_dist * 0.82) % self.length, lateral_offset=side_sign * (exit_w * 0.5 + 4.0)
        )
        p5 = self.get_position(exit_s, lateral_offset=side_sign * (exit_w * 0.45))

        self.pit_control_points = [p1, p2, p3, p4, p5]
        self.pit_lane_enabled = True

        pts = np.array(self.pit_control_points, dtype=np.float64)
        diffs = np.diff(pts, axis=0)
        seg_lens = np.maximum(np.sqrt((diffs**2).sum(axis=1)), 1e-4)
        cum_dist = np.insert(np.cumsum(seg_lens), 0, 0.0)
        self.pit_length = float(cum_dist[-1])

        spline_px = CubicSpline(cum_dist, pts[:, 0])
        spline_py = CubicSpline(cum_dist, pts[:, 1])

        num_pit_samples = max(20, int(self.pit_length / 2.0))
        self.pit_s_samples = np.linspace(0, self.pit_length, num_pit_samples)
        pit_x = spline_px(self.pit_s_samples)
        pit_y = spline_py(self.pit_s_samples)
        self.pit_points = np.column_stack([pit_x, pit_y])

        pdx = spline_px(self.pit_s_samples, 1)
        pdy = spline_py(self.pit_s_samples, 1)
        pspeed = np.maximum(np.sqrt(pdx**2 + pdy**2), 1e-6)
        self.pit_tangents = np.column_stack([pdx / pspeed, pdy / pspeed])

    def get_width(self, s: float) -> float:
        """Returns local track width in meters at distance s."""
        if self.length <= 0 or len(self.widths_sample) == 0:
            return self.width
        s = s % self.length
        idx = int((s / self.length) * len(self.widths_sample)) % len(self.widths_sample)
        return float(self.widths_sample[idx])

    def get_position(self, s: float, lateral_offset: float = 0.0) -> Tuple[float, float]:
        if self.length <= 0 or len(self.points) == 0:
            return (0.0, 0.0)
        s = s % self.length
        idx = int((s / self.length) * len(self.s_samples)) % len(self.s_samples)

        px, py = self.points[idx]
        nx, ny = self.normals[idx]
        return (float(px + nx * lateral_offset), float(py + ny * lateral_offset))

    def get_heading(self, s: float) -> float:
        if self.length <= 0 or len(self.headings) == 0:
            return 0.0
        s = s % self.length
        idx = int((s / self.length) * len(self.s_samples)) % len(self.s_samples)
        return float(self.headings[idx])

    def get_curvature(self, s: float) -> float:
        if self.length <= 0 or len(self.curvatures) == 0:
            return 0.0
        s = s % self.length
        idx = int((s / self.length) * len(self.s_samples)) % len(self.s_samples)
        return float(self.curvatures[idx])

    def get_signed_curvature(self, s: float) -> float:
        if self.length <= 0 or len(self.signed_curvatures) == 0:
            return 0.0
        s = s % self.length
        idx = int((s / self.length) * len(self.s_samples)) % len(self.s_samples)
        return float(self.signed_curvatures[idx])

    def get_corner_apex_ahead(self, s: float, lookahead_m: float = 180.0) -> Tuple[float, float, float]:
        """
        Looks ahead along the circuit up to lookahead_m to find the primary upcoming corner apex.
        Returns: (dist_to_apex, peak_curvature, inside_sign)
        inside_sign: +1.0 if inside is in +normal direction, -1.0 if -normal.
        """
        if self.length <= 0 or len(self.curvatures) == 0:
            return (lookahead_m, 0.0, 1.0)

        step_m = max(2.0, self.sample_step)
        num_steps = max(1, int(lookahead_m / step_m))

        peak_curv = 0.0
        apex_dist = lookahead_m
        apex_signed = 0.0

        # Scan ahead along track for the immediate upcoming corner apex
        for i in range(1, num_steps + 1):
            scan_dist = i * step_m
            scan_s = (s + scan_dist) % self.length
            curv = self.get_curvature(scan_s)

            if curv > 0.003:
                if curv > peak_curv:
                    peak_curv = curv
                    apex_dist = scan_dist
                    apex_signed = self.get_signed_curvature(scan_s)
                elif peak_curv > 0.004 and curv < peak_curv * 0.94:
                    # We have found and passed the first upcoming corner's apex
                    break

        inside_sign = 1.0 if apex_signed >= 0 else -1.0
        return (apex_dist, peak_curv, inside_sign)

    def get_inside_outside_offsets(self, s: float, margin_ratio: float = 0.28) -> Tuple[float, float]:
        """Returns (inside_lateral_offset, outside_lateral_offset) for the corner at distance s."""
        w = self.get_width(s)
        signed_c = self.get_signed_curvature(s)
        inside_sign = 1.0 if signed_c >= 0 else -1.0
        inside_offset = inside_sign * (w * margin_ratio)
        outside_offset = -inside_sign * (w * margin_ratio)
        return (inside_offset, outside_offset)

    def get_racing_line_offset(self, s: float) -> float:
        """
        Calculates optimal geometric racing line lateral offset (Out-In-Out progression).
        In straights -> 0.0 (center)
        In corner approach -> outside entry (+/-)
        At apex -> inside apex corridor
        On exit -> outside sweep
        """
        if self.length <= 0 or len(self.curvatures) == 0:
            return 0.0

        curv = self.get_curvature(s)
        w = self.get_width(s)
        dist_to_apex, apex_curv, inside_sign = self.get_corner_apex_ahead(s, lookahead_m=120.0)

        if apex_curv < 0.003 and curv < 0.003:
            return 0.0  # Straight line

        # Approaching corner: swing wide (outside)
        if dist_to_apex > 35.0:
            outside_sign = -inside_sign
            return outside_sign * (w * 0.26)
        # Clipping apex (within 35m of apex peak): hug inside curb
        elif dist_to_apex <= 15.0 or curv > 0.005:
            return inside_sign * (w * 0.28)
        # Transition into apex
        else:
            interp = (dist_to_apex - 15.0) / 20.0
            return (inside_sign * (1.0 - interp) - inside_sign * interp) * (w * 0.26)

    def get_pit_side_sign(self) -> float:
        """Returns lateral direction multiplier for the pit entry: -1.0 for inside, +1.0 for outside."""
        return -1.0 if self.pit_side == "INSIDE" else 1.0

    def get_pit_approach_racing_line_offset(self, s: float, transition_window_m: float = 65.0) -> float:
        """
        Calculates a smooth transition lateral offset as the car approaches the pit entry node.
        Seamlessly moves the car from the standard racing line toward the pit lane entry corridor
        on the edge of the circuit asphalt without any teleportation or jarring snap.
        """
        if not self.pit_lane_enabled or self.length <= 0:
            return self.get_racing_line_offset(s)

        dist_to_entry = (self.pit_entry_s - s) % self.length
        if dist_to_entry > transition_window_m:
            return self.get_racing_line_offset(s)

        # Fraction along the transition corridor: 1.0 (start of transition) down to 0.0 (at pit entry)
        t = max(0.0, min(1.0, dist_to_entry / transition_window_m))
        normal_offset = self.get_racing_line_offset(s)
        entry_target_offset = self.get_pit_side_sign() * (self.get_width(s) * 0.45)
        # Smooth hermite/cosine interpolation
        smooth_t = 0.5 * (1.0 - math.cos(t * math.pi))
        return smooth_t * normal_offset + (1.0 - smooth_t) * entry_target_offset

    def get_pit_position(self, s_pit: float) -> Tuple[float, float, float]:
        if self.pit_length <= 0 or len(self.pit_points) == 0:
            return (0.0, 0.0, 0.0)
        s_pit = max(0.0, min(s_pit, self.pit_length))
        n_pts = len(self.pit_points)
        raw_idx = (s_pit / self.pit_length) * (n_pts - 1)
        idx = int(raw_idx)
        frac = raw_idx - idx

        if idx >= n_pts - 1:
            px, py = self.pit_points[-1]
            tx, ty = self.pit_tangents[-1]
        else:
            p0 = self.pit_points[idx]
            p1 = self.pit_points[idx + 1]
            px = p0[0] + (p1[0] - p0[0]) * frac
            py = p0[1] + (p1[1] - p0[1]) * frac
            t0 = self.pit_tangents[idx]
            t1 = self.pit_tangents[idx + 1]
            tx = t0[0] + (t1[0] - t0[0]) * frac
            ty = t0[1] + (t1[1] - t0[1]) * frac

        heading = math.atan2(ty, tx)
        return (float(px), float(py), heading)

    def is_in_drs(self, s: float) -> bool:
        s = s % self.length
        for zone in self.drs_zones:
            start = zone.get("start_s", 0.0)
            end = zone.get("end_s", 0.0)
            if start <= end:
                if start <= s <= end:
                    return True
            else:
                if s >= start or s <= end:
                    return True
        return False

    def get_sector(self, s: float) -> int:
        s = s % self.length
        s1_dist = self.sectors[0] * self.length
        s2_dist = self.sectors[1] * self.length
        if s < s1_dist:
            return 1
        elif s < s2_dist:
            return 2
        return 3

    def get_corners(
        self, min_peak_curv: float = 0.0035, min_turn_angle_deg: float = 7.0, min_separation_m: float = 35.0
    ) -> List[Dict]:
        """
        Detects true racing corners along the circuit based on curvature peaks and integrated turn angles.
        Small kinks, micro-bends, and almost-straight sections are excluded and treated as straights.
        Returns list of dicts: [{'apex_s': float, 'min_radius': float, 'turn_angle_deg': float, 'start_s': float, 'end_s': float}]
        """
        corners = []
        if self.length <= 0 or len(self.curvatures) == 0:
            return corners

        n = len(self.s_samples)
        step = self.length / n
        curvs = self.curvatures

        # Find prominent curvature peaks that exceed min_peak_curv
        raw_peaks = []
        for i in range(n):
            k = curvs[i]
            if k >= min_peak_curv and k > curvs[(i - 1) % n] and k >= curvs[(i + 1) % n]:
                raw_peaks.append((i, self.s_samples[i], k))

        # Merge close peaks within min_separation_m
        filtered_peaks = []
        for p_idx, p_s, p_k in raw_peaks:
            if not filtered_peaks:
                filtered_peaks.append((p_idx, p_s, p_k))
            else:
                last_idx, last_s, last_k = filtered_peaks[-1]
                dist = (p_s - last_s) % self.length
                if dist < min_separation_m:
                    if p_k > last_k:
                        filtered_peaks[-1] = (p_idx, p_s, p_k)
                else:
                    filtered_peaks.append((p_idx, p_s, p_k))

        # Check wraparound between last and first
        if len(filtered_peaks) > 1:
            wrap_dist = (filtered_peaks[0][1] - filtered_peaks[-1][1]) % self.length
            if wrap_dist < min_separation_m:
                if filtered_peaks[-1][2] > filtered_peaks[0][2]:
                    filtered_peaks[0] = filtered_peaks[-1]
                filtered_peaks.pop()

        # Measure integrated turning angle across each corner apex
        half_window = max(10, int(45.0 / step))  # +/- 45m window around apex
        for p_idx, p_s, p_k in filtered_peaks:
            angle_accum = 0.0
            for offset in range(-half_window, half_window + 1):
                idx = (p_idx + offset) % n
                angle_accum += curvs[idx] * step
            turn_deg = math.degrees(angle_accum)
            if turn_deg >= min_turn_angle_deg:
                start_s = (p_s - half_window * step) % self.length
                end_s = (p_s + half_window * step) % self.length
                corners.append(
                    {
                        "apex_s": round(p_s, 1),
                        "peak_curv": float(p_k),
                        "min_radius": round(float(1.0 / p_k), 1),
                        "turn_angle_deg": round(float(turn_deg), 1),
                        "start_s": round(start_s, 1),
                        "end_s": round(end_s, 1),
                    }
                )

        corners.sort(key=lambda x: x["apex_s"])
        return corners

    @property
    def corners_count(self) -> int:
        """Returns the number of genuine racing corners on the circuit."""
        return len(self.get_corners())

    def get_turn_node_indices(self) -> Dict[int, int]:
        """
        Maps control point node indices to sequential Turn numbers (1, 2, 3...).
        Straight guidance nodes return None or are omitted, so only genuine corner
        control points are highlighted as race checkpoints/turns.
        Returns: {node_index: turn_number}
        """
        corners = self.get_corners()
        if not corners or not self.node_s_distances:
            return {}

        turn_map = {}
        for turn_num, c_info in enumerate(corners, start=1):
            apex_s = c_info["apex_s"]
            # Find closest control node to apex
            best_idx = min(
                range(len(self.node_s_distances)),
                key=lambda i: min(
                    abs(self.node_s_distances[i] - apex_s), abs(self.length - abs(self.node_s_distances[i] - apex_s))
                ),
            )
            # If multiple apexes map to same node, keep turn number
            if best_idx not in turn_map:
                turn_map[best_idx] = turn_num
        return turn_map

    def get_dry_compounds(self) -> List[str]:
        compound_order = ["HARD", "MEDIUM", "SOFT", "SUPERSOFT", "HYPERSOFT"]
        valid = [c for c in compound_order if c in self.nominated_compounds]
        if len(valid) >= 3:
            return valid[:3]
        return ["HARD", "MEDIUM", "SOFT"]

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "width": self.width,
            "control_points": self.control_points,
            "node_widths": self.node_widths,
            "sectors": self.sectors,
            "drs_zones": self.drs_zones,
            "nominated_compounds": self.nominated_compounds,
            "base_rain_chance": self.base_rain_chance,
            "pit_entry_node": self.pit_entry_node,
            "pit_exit_node": self.pit_exit_node,
            "pit_side": self.pit_side,
            "pit_offset_m": self.pit_offset_m,
            "pit_entry_s": self.pit_entry_s,
            "pit_exit_s": self.pit_exit_s,
            "pit_control_points": self.pit_control_points,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Circuit":
        circuit = cls(name=data.get("name", "Custom Circuit"), width=data.get("width", 14.0))
        circuit.sectors = data.get("sectors", [0.33, 0.66, 1.0])
        circuit.drs_zones = data.get("drs_zones", [])
        circuit.nominated_compounds = data.get("nominated_compounds", ["HARD", "SOFT", "SUPERSOFT"])
        circuit.base_rain_chance = float(data.get("base_rain_chance", 0.20))
        circuit.pit_entry_node = data.get("pit_entry_node", 7)
        circuit.pit_exit_node = data.get("pit_exit_node", 1)
        circuit.pit_side = data.get("pit_side", "INSIDE")
        circuit.pit_offset_m = data.get("pit_offset_m", 14.0)

        pts = data.get("control_points", [])
        widths = data.get("node_widths", None)
        circuit.set_control_points(pts, widths)
        return circuit

    def save_json(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, filepath: str) -> "Circuit":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
