import math
import requests
from typing import List, Tuple, Dict, Optional
from .circuit import Circuit

class OSMImporter:
    """
    Imports and converts OpenStreetMap road nodes and GPS coordinates 
    (Lat, Lon) into continuous 2D Circuit splines using Spherical Mercator projection.
    """
    
    @staticmethod
    def latlon_to_meters(lat: float, lon: float, origin_lat: float, origin_lon: float) -> Tuple[float, float]:
        """Projects (lat, lon) to local tangent plane in meters relative to origin."""
        R = 6378137.0  # WGS84 Earth radius in meters
        d_lat = math.radians(lat - origin_lat)
        d_lon = math.radians(lon - origin_lon)
        lat_rad = math.radians(origin_lat)
        
        x = R * d_lon * math.cos(lat_rad)
        y = -R * d_lat  # Invert Y so North is Up
        return (x, y)

    @classmethod
    def from_coordinates_list(cls, name: str, coords: List[Tuple[float, float]], width: float = 12.0) -> Circuit:
        """
        Creates a Circuit from a list of (lat, lon) GPS coordinates.
        Automatically centers the track at (0, 0).
        """
        if len(coords) < 3:
            raise ValueError("Need at least 3 GPS coordinates to create a circuit.")

        # Compute centroid as projection origin
        avg_lat = sum(p[0] for p in coords) / len(coords)
        avg_lon = sum(p[1] for p in coords) / len(coords)

        # Convert to local meters
        local_points = [cls.latlon_to_meters(lat, lon, avg_lat, avg_lon) for lat, lon in coords]
        
        circuit = Circuit(name=name, width=width)
        circuit.set_control_points(local_points)
        return circuit

    @classmethod
    def fetch_overpass_street_loop(cls, query_bbox: Tuple[float, float, float, float], 
                                  street_names: Optional[List[str]] = None) -> Optional[List[Tuple[float, float]]]:
        """
        Fetches street nodes within a bounding box (south, west, north, east) from OpenStreetMap Overpass API.
        """
        s, w, n, e = query_bbox
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:15];
        (
          way["highway"~"primary|secondary|tertiary|residential"]({s},{w},{n},{e});
        );
        out body;
        >;
        out skel qt;
        """
        try:
            resp = requests.post(overpass_url, data={"data": query}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                nodes = {node["id"]: (node["lat"], node["lon"]) for node in data.get("elements", []) if node["type"] == "node"}
                ways = [way["nodes"] for way in data.get("elements", []) if way["type"] == "way"]
                
                # Extract first prominent way loop if available
                if ways:
                    coords = [nodes[nid] for nid in ways[0] if nid in nodes]
                    return coords
        except Exception as ex:
            print(f"OSM query note: {ex}")
        return None
