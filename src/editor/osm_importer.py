"""
OSM Importer module for race-game Track Editor.
Provides geocoding, road network querying via Overpass API, local disk caching,
GPS-to-meters projection, road snapping, and Circuit object generation.
Completely copyright-free: no hardcoded or bundled real-world circuits.
"""

import heapq
import json
import math
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.core.circuit import Circuit

EARTH_RADIUS = 6371000.0  # meters
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "osm_cache")


def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)


ROAD_TYPE_DEFAULT_WIDTHS: Dict[str, float] = {
    "motorway": 20.0,
    "motorway_link": 14.0,
    "trunk": 16.0,
    "trunk_link": 12.0,
    "primary": 15.0,
    "primary_link": 12.0,
    "secondary": 13.0,
    "secondary_link": 11.0,
    "tertiary": 11.0,
    "tertiary_link": 10.0,
    "unclassified": 9.5,
    "residential": 9.0,
    "living_street": 8.0,
    "service": 8.0,
    "pedestrian": 10.0,
    "cycleway": 7.5,
    "track": 7.5,
    "path": 7.5,
    "road": 11.0,
}


def parse_osm_road_width(tags: Dict[str, Any]) -> float:
    """
    Extracts or estimates realistic road width (in meters) from OSM tags:
    1. Explicit 'width' or 'est_width' tag (e.g. '7.5', '12 m', '6,5')
    2. Number of lanes 'lanes' tag (e.g. '2' -> ~11.0m, '4' -> ~18.0m)
    3. Road classification fallback hierarchy ('motorway', 'primary', 'residential', etc.)
    Clamped to [7.0m, 30.0m] for realistic racing physics.
    """
    if not isinstance(tags, dict):
        return 11.0

    # 1. Try explicit 'width' or 'est_width'
    for key in ("width", "est_width"):
        val = tags.get(key)
        if val is not None:
            val_str = (
                str(val).lower().replace("m", "").replace("meters", "").replace("metres", "").replace(",", ".").strip()
            )
            val_str = val_str.split(";")[0].split()[0] if val_str else ""
            try:
                w_val = float(val_str)
                if 2.5 <= w_val <= 45.0:
                    return round(max(7.0, min(30.0, w_val)), 2)
            except ValueError:
                # Value could not be parsed as float, proceed to next tag
                pass

    # 2. Try 'lanes' tag
    lanes_val = tags.get("lanes")
    if lanes_val is not None:
        lanes_str = str(lanes_val).split(";")[0].strip()
        try:
            lanes = int(float(lanes_str))
            if lanes >= 1:
                # 1 lane: 7.5m, 2 lanes: 11.0m, 3 lanes: 14.5m, 4 lanes: 18.0m...
                calculated_w = max(7.5, lanes * 3.5 + 4.0)
                return round(max(7.0, min(30.0, calculated_w)), 2)
        except ValueError:
            # Value could not be parsed as int/float, fall back to highway classification
            pass

    # 3. Fallback based on road classification
    highway_type = tags.get("highway") or tags.get("type") or "road"
    if isinstance(highway_type, str):
        highway_type = highway_type.lower().strip()
    return ROAD_TYPE_DEFAULT_WIDTHS.get(highway_type, 11.0)


def project_gps_to_meters(lat: float, lon: float, lat0: float, lon0: float) -> Tuple[float, float]:
    """
    Equirectangular projection centered at (lat0, lon0).
    Returns (x, y) in meters.
    x: Easting (+)
    y: Northing (-) so that North is upwards in typical Pygame 2D canvas.
    """
    lat0_rad = math.radians(lat0)
    d_lon_rad = math.radians(lon - lon0)
    d_lat_rad = math.radians(lat - lat0)

    x = EARTH_RADIUS * d_lon_rad * math.cos(lat0_rad)
    y = -EARTH_RADIUS * d_lat_rad
    return (round(x, 2), round(y, 2))


def unproject_meters_to_gps(x: float, y: float, lat0: float, lon0: float) -> Tuple[float, float]:
    """
    Inverse equirectangular projection centered at (lat0, lon0).
    Returns (lat, lon) in degrees.
    """
    lat0_rad = math.radians(lat0)
    d_lat_rad = -y / EARTH_RADIUS
    cos_lat0 = math.cos(lat0_rad)
    d_lon_rad = x / (EARTH_RADIUS * cos_lat0) if abs(cos_lat0) > 1e-6 else 0.0

    lat = lat0 + math.degrees(d_lat_rad)
    lon = lon0 + math.degrees(d_lon_rad)
    return (round(lat, 6), round(lon, 6))


def geocode_location(query: str) -> Optional[Dict[str, Any]]:
    """
    Geocode a location query string using OpenStreetMap Nominatim.
    Returns dict with 'lat', 'lon', 'display_name' or None.
    """
    if not query.strip():
        return None

    encoded_q = urllib.parse.quote(query.strip())
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_q}&format=json&limit=1"
    headers = {"User-Agent": "RaceGameTrackEditor/1.0 (Educational open-source project)"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and len(data) > 0:
                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", query),
                }
    except Exception as e:
        print(f"[OSMImporter] Geocoding error for '{query}': {e}")
    return None


OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def fetch_road_network(
    lat: float, lon: float, radius_m: int = 1500, origin_lat: Optional[float] = None, origin_lon: Optional[float] = None
) -> Dict[str, Any]:
    """
    Fetches drivable roads and cycling/path networks around (lat, lon) within radius_m using Overpass API.
    Caches response locally to avoid redundant API calls.
    Points are projected relative to (origin_lat, origin_lon) if specified, otherwise (lat, lon).
    Rotates through multiple Overpass mirror endpoints if rate limited (HTTP 429) or timed out.
    Returns processed road network data.
    """
    ensure_cache_dir()
    cache_filename = f"osm_{round(lat, 4)}_{round(lon, 4)}_{radius_m}.json"
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    proj_lat0 = origin_lat if origin_lat is not None else lat
    proj_lon0 = origin_lon if origin_lon is not None else lon

    raw_data = None
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                # If cached data already has ways with points_gps, reproject to proj_lat0, proj_lon0
                if "ways" in cached_data and cached_data["ways"]:
                    reprojected_ways = []
                    for w in cached_data["ways"]:
                        w_copy = dict(w)
                        if "width_m" not in w_copy:
                            w_tags = w.get("tags") or {"highway": w.get("type", "road")}
                            w_copy["width_m"] = parse_osm_road_width(w_tags)
                        gps_pts = w.get("points_gps", [])
                        if gps_pts:
                            xy_pts = [project_gps_to_meters(glat, glon, proj_lat0, proj_lon0) for glat, glon in gps_pts]
                            w_copy["points_xy"] = xy_pts
                            xs = [p[0] for p in xy_pts]
                            ys = [p[1] for p in xy_pts]
                            w_copy["bbox"] = (min(xs), max(xs), min(ys), max(ys))
                            reprojected_ways.append(w_copy)
                        else:
                            xy_pts = w.get("points_xy", [])
                            if xy_pts:
                                xs = [p[0] for p in xy_pts]
                                ys = [p[1] for p in xy_pts]
                                w_copy["bbox"] = (min(xs), max(xs), min(ys), max(ys))
                            reprojected_ways.append(w_copy)
                    return {"center": [lat, lon], "radius": radius_m, "ways": reprojected_ways}
        except Exception:
            # Cache read/deserialization failed, proceed to live query
            pass

    # Build Overpass QL query covering all drivable roads as well as cycleways, bike highways, paths, and service tracks
    highway_filter = (
        "motorway|trunk|primary|secondary|tertiary|unclassified|residential|service|living_street|cycleway|track|path"
    )
    overpass_query = f"""
    [out:json][timeout:25];
    (
      way["highway"~"{highway_filter}"](around:{radius_m},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """

    data_payload = urllib.parse.urlencode({"data": overpass_query}).encode("utf-8")
    headers = {
        "User-Agent": "RaceGameTrackEditor/1.0 (Educational open-source project; contact: github.com/personal/race-game)"
    }

    last_error = None
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            req = urllib.request.Request(endpoint, data=data_payload, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw_data = json.loads(resp.read().decode("utf-8"))
                if raw_data:
                    break
        except Exception as e:
            last_error = e
            print(f"[OSMImporter] Overpass endpoint {endpoint} failed ({e}), trying next mirror...")

    if not raw_data:
        print(f"[OSMImporter] All Overpass endpoints failed. Last error: {last_error}")
        return {"center": [lat, lon], "radius": radius_m, "ways": []}

    # Parse nodes and ways
    nodes = {}
    for element in raw_data.get("elements", []):
        if element.get("type") == "node":
            nodes[element["id"]] = (element["lat"], element["lon"])

    ways = []
    for element in raw_data.get("elements", []):
        if element.get("type") == "way" and "nodes" in element:
            tags = element.get("tags", {})
            way_nodes = element["nodes"]
            points_gps = []
            points_xy = []
            for nid in way_nodes:
                if nid in nodes:
                    nlat, nlon = nodes[nid]
                    points_gps.append((nlat, nlon))
                    xy = project_gps_to_meters(nlat, nlon, proj_lat0, proj_lon0)
                    points_xy.append(xy)

            if len(points_xy) >= 2:
                xs = [p[0] for p in points_xy]
                ys = [p[1] for p in points_xy]
                road_type = tags.get("highway", "road")
                ways.append(
                    {
                        "id": element["id"],
                        "name": tags.get("name", "Unnamed Road"),
                        "type": road_type,
                        "width_m": parse_osm_road_width(tags),
                        "tags": tags,
                        "oneway": tags.get("oneway") in ["yes", "1", "true"],
                        "points_gps": points_gps,
                        "points_xy": points_xy,
                        "bbox": (min(xs), max(xs), min(ys), max(ys)),
                    }
                )

    result = {"center": [lat, lon], "radius": radius_m, "ways": ways}

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f)
    except Exception as e:
        print(f"[OSMImporter] Cache write failed: {e}")

    return result


def point_segment_distance(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> Tuple[float, Tuple[float, float]]:
    """
    Returns (distance, (closest_x, closest_y)) from point P to segment AB.
    """
    dx = bx - ax
    dy = by - ay
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0.0:
        dist = math.hypot(px - ax, py - ay)
        return dist, (ax, ay)

    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    dist = math.hypot(px - proj_x, py - proj_y)
    return dist, (round(proj_x, 2), round(proj_y, 2))


def snap_point_to_roads(
    px: float, py: float, ways: List[Dict[str, Any]], max_dist: float = 80.0
) -> Optional[Dict[str, Any]]:
    """
    Finds closest point on any road segment within max_dist meters.
    """
    best_dist = float("inf")
    best_pt = None
    best_road = None

    for way in ways:
        bbox = way.get("bbox")
        if bbox:
            min_x, max_x, min_y, max_y = bbox
            if px < min_x - max_dist or px > max_x + max_dist or py < min_y - max_dist or py > max_y + max_dist:
                continue

        pts = way["points_xy"]
        for i in range(len(pts) - 1):
            ax, ay = pts[i]
            bx, by = pts[i + 1]
            d, proj = point_segment_distance(px, py, ax, ay, bx, by)
            if d < best_dist and d <= max_dist:
                best_dist = d
                best_pt = proj
                best_road = way

    if best_pt and best_road:
        road_w = best_road.get("width_m")
        if road_w is None:
            road_w = parse_osm_road_width(best_road.get("tags") or {"highway": best_road.get("type", "road")})
        return {
            "snapped_xy": best_pt,
            "road_name": best_road["name"],
            "road_type": best_road["type"],
            "width_m": float(road_w),
            "distance": best_dist,
        }
    return None


def remove_backtracking_and_hairpins(path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Removes artificial 180-degree turnarounds, spurs, and doubling back along road segments.
    Preserves true gentle corners and curved racing hairpins.
    """
    if len(path) < 3:
        return path

    pts = list(path)
    changed = True
    iterations = 0
    while changed and len(pts) >= 3 and iterations < 10:
        changed = False
        iterations += 1
        new_pts = [pts[0]]
        i = 1
        while i < len(pts) - 1:
            p_prev = new_pts[-1]
            p_curr = pts[i]
            p_next = pts[i + 1]

            # Drop micro-duplicate points
            if math.hypot(p_curr[0] - p_prev[0], p_curr[1] - p_prev[1]) < 1.0:
                changed = True
                i += 1
                continue
            if math.hypot(p_next[0] - p_curr[0], p_next[1] - p_curr[1]) < 1.0:
                changed = True
                i += 1
                continue

            v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
            v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
            len1 = math.hypot(v1[0], v1[1])
            len2 = math.hypot(v2[0], v2[1])

            if len1 > 1e-3 and len2 > 1e-3:
                cos_a = (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)
                # Angle > 120 deg reversal (doubling back along the incoming road)
                if cos_a < -0.50:
                    changed = True
                    i += 1
                    continue

            new_pts.append(p_curr)
            i += 1
        new_pts.append(pts[-1])

        # Deduplicate consecutive identical points
        dedup = [new_pts[0]]
        for p in new_pts[1:]:
            if math.hypot(p[0] - dedup[-1][0], p[1] - dedup[-1][1]) >= 1.0:
                dedup.append(p)
        pts = dedup

    return pts


def simplify_almost_straights(
    pts: List[Tuple[float, float]], max_lateral_dev: float = 3.5, min_corner_angle_deg: float = 10.0
) -> List[Tuple[float, float]]:
    """
    Simplifies road geometry by collapsing small kinks, micro-bends, and sub-threshold wiggles
    that are almost straight in reality (e.g. slight road surveying noise or gentle street swerves).
    Points deviating laterally by less than max_lateral_dev meters from a chord or forming an
    angle under min_corner_angle_deg are treated as straight road sections.
    """
    if len(pts) < 4:
        return pts

    # Ramer-Douglas-Peucker simplification using perpendicular distance to chord
    def _rdp(sub: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        if len(sub) < 3:
            return sub
        p1, p2 = sub[0], sub[-1]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        l_sq = dx * dx + dy * dy
        dmax = 0.0
        index = 0
        for i in range(1, len(sub) - 1):
            p = sub[i]
            if l_sq < 1e-6:
                d = math.hypot(p[0] - p1[0], p[1] - p1[1])
            else:
                t = max(0.0, min(1.0, ((p[0] - p1[0]) * dx + (p[1] - p1[1]) * dy) / l_sq))
                px = p1[0] + t * dx
                py = p1[1] + t * dy
                d = math.hypot(p[0] - px, p[1] - py)
            if d > dmax:
                index = i
                dmax = d
        if dmax > max_lateral_dev:
            r1 = _rdp(sub[: index + 1])
            r2 = _rdp(sub[index:])
            return r1[:-1] + r2
        else:
            return [sub[0], sub[-1]]

    simp = _rdp(pts)
    if len(simp) < 4:
        return simp

    # Secondary pass: prune intermediate vertices where cumulative deflection < min_corner_angle_deg
    res = [simp[0]]
    for i in range(1, len(simp) - 1):
        p_prev = res[-1]
        p_curr = simp[i]
        p_next = simp[i + 1]
        dx1, dy1 = p_curr[0] - p_prev[0], p_curr[1] - p_prev[1]
        dx2, dy2 = p_next[0] - p_curr[0], p_next[1] - p_curr[1]
        l1 = math.hypot(dx1, dy1)
        l2 = math.hypot(dx2, dy2)
        if l1 < 8.0 or l2 < 8.0:
            continue
        dot = max(-1.0, min(1.0, (dx1 * dx2 + dy1 * dy2) / (l1 * l2)))
        angle_deg = math.degrees(math.acos(dot))
        if angle_deg >= min_corner_angle_deg:
            res.append(p_curr)
    res.append(simp[-1])
    return res


def fillet_sharp_corners(pts: List[Tuple[float, float]], default_radius: float = 14.0) -> List[Tuple[float, float]]:
    """
    Smooths sharp knife-edge intersection turns (e.g. 90-degree street corners) by inserting
    a smooth 3-point transition arc (entry, apex, exit), preventing CubicSpline overshoot.
    """
    n = len(pts)
    if n < 3:
        return pts

    result = []
    for i in range(n):
        p_prev = np.array(pts[(i - 1) % n], dtype=float)
        p_curr = np.array(pts[i], dtype=float)
        p_next = np.array(pts[(i + 1) % n], dtype=float)

        v_in = p_curr - p_prev
        v_out = p_next - p_curr
        l_in = np.linalg.norm(v_in)
        l_out = np.linalg.norm(v_out)

        if l_in < 1e-3 or l_out < 1e-3:
            result.append((round(float(p_curr[0]), 2), round(float(p_curr[1]), 2)))
            continue

        u_in = v_in / l_in
        u_out = v_out / l_out

        dot = np.clip(np.dot(u_in, u_out), -1.0, 1.0)
        deflection = math.acos(dot)

        # Fillet corners with noticeable turn (between 25 deg and 145 deg)
        if math.radians(25) <= deflection <= math.radians(145):
            d = min(default_radius * math.tan(deflection / 2.0), min(l_in, l_out) * 0.40)
            t1 = p_curr - u_in * d
            t2 = p_curr + u_out * d
            apex = 0.25 * t1 + 0.5 * p_curr + 0.25 * t2

            result.append((round(float(t1[0]), 2), round(float(t1[1]), 2)))
            result.append((round(float(apex[0]), 2), round(float(apex[1]), 2)))
            result.append((round(float(t2[0]), 2), round(float(t2[1]), 2)))
        else:
            result.append((round(float(p_curr[0]), 2), round(float(p_curr[1]), 2)))

    return result


def regularize_control_points(
    pts: List[Tuple[float, float]], min_spacing: float = 20.0, max_spacing: Optional[float] = None
) -> List[Tuple[float, float]]:
    """
    Cleans and deduplicates control points:
    - Eliminates micro-spaced redundant points closer than min_spacing.
    - Preserves straight lines cleanly without adding artificial intermediate dots.
    """
    if len(pts) < 4:
        return pts

    filtered = [pts[0]]
    for p in pts[1:]:
        d = math.hypot(p[0] - filtered[-1][0], p[1] - filtered[-1][1])
        if d >= min_spacing:
            filtered.append(p)

    if len(filtered) > 4:
        d_close = math.hypot(filtered[-1][0] - filtered[0][0], filtered[-1][1] - filtered[0][1])
        if d_close < min_spacing:
            filtered.pop()

    if not max_spacing:
        return filtered

    res = []
    n = len(filtered)
    for i in range(n):
        p1 = filtered[i]
        p2 = filtered[(i + 1) % n]
        res.append(p1)
        d = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        if d > max_spacing:
            num_splits = int(math.ceil(d / max_spacing))
            for k in range(1, num_splits):
                t = k / num_splits
                pk = (round(p1[0] + t * (p2[0] - p1[0]), 2), round(p1[1] + t * (p2[1] - p1[1]), 2))
                res.append(pk)
    return res


def shortest_path_on_roads(
    start_pt: Tuple[float, float], end_pt: Tuple[float, float], ways: List[Dict[str, Any]], tolerance: float = 10.0
) -> List[Tuple[float, float]]:
    """
    Finds a sequence of road vertices connecting start_pt to end_pt along the public road network using A* search.
    Splits snapped segments directly at start_pt and end_pt to eliminate 180-degree doubling back.
    Cleans any backtracking or spur artifacts.
    """
    if not ways:
        return [start_pt, end_pt]

    def _coord_key(pt: Tuple[float, float]) -> Tuple[int, int]:
        return (int(round(pt[0] / tolerance)), int(round(pt[1] / tolerance)))

    # Identify closest segment for start_pt and end_pt
    best_start_seg = None
    best_start_d = 60.0
    best_start_proj = start_pt
    best_start_t = 0.0

    best_end_seg = None
    best_end_d = 60.0
    best_end_proj = end_pt
    best_end_t = 0.0

    for w_idx, way in enumerate(ways):
        pts = way["points_xy"]
        for s_idx in range(len(pts) - 1):
            ax, ay = pts[s_idx]
            bx, by = pts[s_idx + 1]
            dx = bx - ax
            dy = by - ay
            seg_len_sq = dx * dx + dy * dy
            if seg_len_sq == 0.0:
                continue

            # Check start_pt
            t_s = max(0.0, min(1.0, ((start_pt[0] - ax) * dx + (start_pt[1] - ay) * dy) / seg_len_sq))
            ps_x = ax + t_s * dx
            ps_y = ay + t_s * dy
            d_s = math.hypot(start_pt[0] - ps_x, start_pt[1] - ps_y)
            if d_s < best_start_d:
                best_start_d = d_s
                best_start_seg = (w_idx, s_idx)
                best_start_proj = (round(ps_x, 2), round(ps_y, 2))
                best_start_t = t_s

            # Check end_pt
            t_e = max(0.0, min(1.0, ((end_pt[0] - ax) * dx + (end_pt[1] - ay) * dy) / seg_len_sq))
            pe_x = ax + t_e * dx
            pe_y = ay + t_e * dy
            d_e = math.hypot(end_pt[0] - pe_x, end_pt[1] - pe_y)
            if d_e < best_end_d:
                best_end_d = d_e
                best_end_seg = (w_idx, s_idx)
                best_end_proj = (round(pe_x, 2), round(pe_y, 2))
                best_end_t = t_e

    # Build road adjacency graph
    adj: Dict[Tuple[int, int], List[Tuple[Tuple[int, int], Tuple[float, float], float]]] = {}
    key_to_exact: Dict[Tuple[int, int], Tuple[float, float]] = {}

    def add_edge(p1: Tuple[float, float], p2: Tuple[float, float]):
        k1 = _coord_key(p1)
        k2 = _coord_key(p2)
        if k1 == k2:
            return
        if k1 not in key_to_exact:
            key_to_exact[k1] = p1
        if k2 not in key_to_exact:
            key_to_exact[k2] = p2
        cost = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        adj.setdefault(k1, []).append((k2, p2, cost))
        adj.setdefault(k2, []).append((k1, p1, cost))

    for w_idx, way in enumerate(ways):
        pts = way["points_xy"]
        for s_idx in range(len(pts) - 1):
            p1 = pts[s_idx]
            p2 = pts[s_idx + 1]
            seg_key = (w_idx, s_idx)

            inter_pts = []
            if seg_key == best_start_seg:
                inter_pts.append((best_start_t, best_start_proj))
            if seg_key == best_end_seg:
                inter_pts.append((best_end_t, best_end_proj))

            if not inter_pts:
                add_edge(p1, p2)
            else:
                inter_pts.sort(key=lambda item: item[0])
                chain = [p1] + [pt for _, pt in inter_pts] + [p2]
                for c_i in range(len(chain) - 1):
                    add_edge(chain[c_i], chain[c_i + 1])

    start_k = _coord_key(best_start_proj)
    end_k = _coord_key(best_end_proj)

    # Fallback to nearest existing node if projection didn't connect
    if start_k not in adj:
        best_d = float("inf")
        for k in adj:
            d = math.hypot(start_pt[0] - key_to_exact[k][0], start_pt[1] - key_to_exact[k][1])
            if d < best_d:
                best_d = d
                start_k = k
    if end_k not in adj:
        best_d = float("inf")
        for k in adj:
            d = math.hypot(end_pt[0] - key_to_exact[k][0], end_pt[1] - key_to_exact[k][1])
            if d < best_d:
                best_d = d
                end_k = k

    if not start_k or not end_k or start_k == end_k or start_k not in adj or end_k not in adj:
        return [start_pt, end_pt]

    # A* Search
    target_pos = key_to_exact[end_k]
    pq = [(0.0, 0.0, start_k)]
    costs: Dict[Tuple[int, int], float] = {start_k: 0.0}
    parents: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start_k: None}

    found = False
    visited_count = 0
    max_steps = 5000

    while pq and visited_count < max_steps:
        f_val, cur_cost, u_k = heapq.heappop(pq)
        visited_count += 1

        if u_k == end_k:
            found = True
            break

        if cur_cost > costs.get(u_k, float("inf")):
            continue

        for v_k, v_exact, edge_cost in adj.get(u_k, []):
            new_cost = cur_cost + edge_cost
            if new_cost < costs.get(v_k, float("inf")):
                costs[v_k] = new_cost
                parents[v_k] = u_k
                h = math.hypot(v_exact[0] - target_pos[0], v_exact[1] - target_pos[1])
                heapq.heappush(pq, (new_cost + h, new_cost, v_k))

    if not found:
        return [start_pt, end_pt]

    # Reconstruct path
    path_nodes = []
    curr = end_k
    while curr is not None:
        path_nodes.append(key_to_exact[curr])
        curr = parents.get(curr)
    path_nodes.reverse()

    # Prepend start_pt and append end_pt if distant
    res = [start_pt]
    for p in path_nodes:
        if math.hypot(p[0] - res[-1][0], p[1] - res[-1][1]) > 3.0:
            res.append(p)
    if math.hypot(end_pt[0] - res[-1][0], end_pt[1] - res[-1][1]) > 3.0:
        res.append(end_pt)

    # Eliminate any 180 backtracking or spurs
    cleaned = remove_backtracking_and_hairpins(res)
    return cleaned


def convert_waypoints_to_circuit(
    waypoints: List[Tuple[float, float]],
    track_name: str = "Custom Street Circuit",
    default_width: float = 12.0,
    min_dist_spacing: float = 12.0,
    ways: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Circuit]:
    """
    Transforms user-selected road waypoints into a complete, drivable Circuit.
    - Eliminates backtracking and 180-degree turnaround artifacts.
    - Fillets sharp intersection turns with smooth transition arcs.
    - Regularizes spline control points to prevent overshoot and Runge oscillations.
    - Samples realistic street widths from OSM road network (narrow alleys to wide boulevards).
    - Centers coordinates around (0, 0).
    - Generates pit lane and DRS zone.
    """
    if len(waypoints) < 4:
        return None

    # 1. Clean backtracking / 180 turnarounds
    cleaned = remove_backtracking_and_hairpins(waypoints)
    if len(cleaned) < 4:
        return None

    # 2. Check closing distance
    first = cleaned[0]
    last = cleaned[-1]
    close_dist = math.hypot(last[0] - first[0], last[1] - first[1])
    if close_dist > 5.0:
        # Close loop
        cleaned.append(first)

    # 3. Simplify almost-straight road segments (collapses micro-wiggles & kinks into true straights)
    simplified = simplify_almost_straights(cleaned, max_lateral_dev=4.5, min_corner_angle_deg=12.0)

    # 4. Fillet sharp intersection corners (replaces knife-edge vertices with smooth 3-point arcs)
    filleted = fillet_sharp_corners(simplified[:-1], default_radius=14.0)

    # 5. Clean control points without subdividing straight lines
    effective_min_spacing = max(min_dist_spacing, 18.0)
    regularized = regularize_control_points(filleted, min_spacing=effective_min_spacing, max_spacing=None)

    if len(regularized) < 5:
        return None

    # 6. Sample local street widths from OSM road network before centering
    raw_widths = []
    if ways:
        for p in regularized:
            snap_res = snap_point_to_roads(p[0], p[1], ways, max_dist=120.0)
            if snap_res and "width_m" in snap_res:
                raw_widths.append(float(snap_res["width_m"]))
            else:
                raw_widths.append(default_width)
    else:
        raw_widths = [default_width] * len(regularized)

    # 7. Smooth node widths with a 3-point circular moving average to prevent abrupt width jumps
    n_pts = len(raw_widths)
    if n_pts >= 3 and ways:
        smoothed_widths = []
        for i in range(n_pts):
            prev_w = raw_widths[(i - 1) % n_pts]
            curr_w = raw_widths[i]
            next_w = raw_widths[(i + 1) % n_pts]
            w_smooth = 0.25 * prev_w + 0.50 * curr_w + 0.25 * next_w
            smoothed_widths.append(round(float(np.clip(w_smooth, 7.0, 28.0)), 2))
        widths = smoothed_widths
    else:
        widths = raw_widths

    # 8. Center coordinates around (0, 0)
    avg_x = sum(p[0] for p in regularized) / len(regularized)
    avg_y = sum(p[1] for p in regularized) / len(regularized)
    centered = [(round(p[0] - avg_x, 2), round(p[1] - avg_y, 2)) for p in regularized]

    # 9. Build Circuit with per-node widths
    avg_width = float(np.mean(widths)) if widths else default_width
    circuit = Circuit(name=track_name, width=round(avg_width, 1))
    circuit.set_control_points(centered, widths)

    # Setup automatic pit lane alongside the start-finish straight
    total_pts = len(centered)
    pit_entry_idx = (total_pts - 2) % total_pts
    pit_exit_idx = 2 % total_pts

    sf_width = widths[0] if widths else default_width
    circuit.set_pit_lane_endpoints(
        entry_node=pit_entry_idx, exit_node=pit_exit_idx, side="INSIDE", offset_m=sf_width * 1.2
    )

    # Setup one DRS zone on the longest straight
    max_straight_len = 0.0
    best_a = 0
    best_b = 1

    if len(circuit.node_s_distances) >= 3:
        for i in range(len(circuit.node_s_distances)):
            next_i = (i + 1) % len(circuit.node_s_distances)
            p1 = circuit.control_points[i]
            p2 = circuit.control_points[next_i]
            dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            if dist > max_straight_len:
                max_straight_len = dist
                best_a = i
                best_b = next_i

        start_s = circuit.node_s_distances[best_a]
        end_s = circuit.node_s_distances[best_b]
        if end_s < start_s:
            end_s = circuit.length
        circuit.drs_zones = [
            {
                "name": f"DRS #{best_a + 1}->#{best_b + 1}",
                "node_a": best_a,
                "node_b": best_b,
                "start_s": start_s,
                "end_s": end_s,
            }
        ]

    return circuit
