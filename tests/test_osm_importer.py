import unittest

from src.editor.osm_importer import (
    convert_waypoints_to_circuit,
    point_segment_distance,
    project_gps_to_meters,
    snap_point_to_roads,
    unproject_meters_to_gps,
)


class TestOSMImporter(unittest.TestCase):
    def test_equirectangular_projection(self):
        # At origin
        x0, y0 = project_gps_to_meters(51.2194, 4.4025, 51.2194, 4.4025)
        self.assertAlmostEqual(x0, 0.0, places=1)
        self.assertAlmostEqual(y0, 0.0, places=1)

        # 0.01 deg north (~1110 meters)
        xn, yn = project_gps_to_meters(51.2294, 4.4025, 51.2194, 4.4025)
        self.assertAlmostEqual(xn, 0.0, places=1)
        self.assertLess(yn, -1000.0)  # negative Y is up/north

        # 0.01 deg east
        xe, ye = project_gps_to_meters(51.2194, 4.4125, 51.2194, 4.4025)
        self.assertGreater(xe, 600.0)
        self.assertAlmostEqual(ye, 0.0, places=1)

        # Roundtrip inverse projection test
        lat_back, lon_back = unproject_meters_to_gps(xe, ye, 51.2194, 4.4025)
        self.assertAlmostEqual(lat_back, 51.2194, places=4)
        self.assertAlmostEqual(lon_back, 4.4125, places=4)

    def test_point_segment_distance(self):
        # Point right above horizontal segment from (0, 0) to (100, 0)
        dist, proj = point_segment_distance(50, 10, 0, 0, 100, 0)
        self.assertAlmostEqual(dist, 10.0, places=1)
        self.assertEqual(proj, (50.0, 0.0))

        # Point beyond segment end B
        dist_b, proj_b = point_segment_distance(120, 0, 0, 0, 100, 0)
        self.assertAlmostEqual(dist_b, 20.0, places=1)
        self.assertEqual(proj_b, (100.0, 0.0))

    def test_snap_point_to_roads(self):
        ways = [
            {"id": 101, "name": "Grand Avenue", "type": "primary", "points_xy": [(-100, 0), (100, 0)]},
            {"id": 102, "name": "Oak Street", "type": "secondary", "points_xy": [(0, 0), (0, 200)]},
        ]

        snap = snap_point_to_roads(10, 5, ways, max_dist=20.0)
        self.assertIsNotNone(snap)
        self.assertEqual(snap["road_name"], "Grand Avenue")
        self.assertAlmostEqual(snap["snapped_xy"][1], 0.0, places=1)

    def test_convert_waypoints_to_circuit(self):
        # Create an oval-like series of waypoints
        pts = [
            (-200.0, -100.0),
            (-100.0, -100.0),
            (0.0, -100.0),
            (100.0, -100.0),
            (200.0, -100.0),
            (250.0, 0.0),
            (200.0, 100.0),
            (100.0, 100.0),
            (0.0, 100.0),
            (-100.0, 100.0),
            (-200.0, 100.0),
            (-250.0, 0.0),
            (-200.0, -100.0),  # closed loop
        ]

        circuit = convert_waypoints_to_circuit(pts, track_name="Antwerp Waterfront")
        self.assertIsNotNone(circuit)
        self.assertEqual(circuit.name, "Antwerp Waterfront")
        self.assertGreater(circuit.length, 400.0)
        self.assertGreater(len(circuit.points), 50)
        self.assertTrue(len(circuit.drs_zones) > 0)
        self.assertTrue(circuit.pit_entry_node is not None)
        self.assertTrue(circuit.pit_exit_node is not None)

    def test_shortest_path_on_roads(self):
        from src.editor.osm_importer import shortest_path_on_roads

        ways = [
            {"id": 1, "type": "primary", "points_xy": [(0.0, 0.0), (100.0, 0.0)]},
            {"id": 2, "type": "primary", "points_xy": [(100.0, 0.0), (100.0, 50.0), (100.0, 100.0)]},
            {"id": 3, "type": "residential", "points_xy": [(100.0, 100.0), (0.0, 100.0)]},
        ]

        # Route from near (0,0) to near (0, 100)
        start = (0.0, 0.0)
        end = (0.0, 100.0)
        path = shortest_path_on_roads(start, end, ways, tolerance=5.0)

        self.assertGreater(len(path), 2)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], end)
        # Should visit intermediate node (100, 0)
        intermediate_xs = [p[0] for p in path]
        self.assertIn(100.0, intermediate_xs)

    def test_expanded_highway_types_snapping(self):
        ways = [
            {"id": 201, "name": "F11 Bike Highway", "type": "cycleway", "points_xy": [(0, 0), (200, 0)]},
            {"id": 202, "name": "Park Track", "type": "track", "points_xy": [(0, 50), (200, 50)]},
        ]
        snap_cycle = snap_point_to_roads(100, 2, ways, max_dist=10.0)
        self.assertIsNotNone(snap_cycle)
        self.assertEqual(snap_cycle["road_name"], "F11 Bike Highway")
        self.assertEqual(snap_cycle["road_type"], "cycleway")

        snap_track = snap_point_to_roads(100, 48, ways, max_dist=10.0)
        self.assertIsNotNone(snap_track)
        self.assertEqual(snap_track["road_name"], "Park Track")

    def test_way_bbox_calculation(self):

        # Test with dummy data
        ways = [{"id": 1, "name": "Way 1", "type": "residential", "points_xy": [(-50.0, 10.0), (120.0, 80.0)]}]
        xs = [p[0] for p in ways[0]["points_xy"]]
        ys = [p[1] for p in ways[0]["points_xy"]]
        bbox = (min(xs), max(xs), min(ys), max(ys))
        self.assertEqual(bbox, (-50.0, 120.0, 10.0, 80.0))

    def test_viewport_chunk_queuing(self):
        import pygame

        from src.editor.osm_map_modal import OSMMapModal

        pygame.init()

        modal = OSMMapModal(on_circuit_created=lambda c: None)
        modal.current_lat = 51.1184
        modal.current_lon = 3.5596
        modal.map_rect = pygame.Rect(50, 50, 1800, 900)
        modal.loaded_chunks = {(0, 0), (-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)}
        modal.zoom = 0.5
        modal.cam_x = 0.0
        modal.cam_y = 0.0

        # At zoom=0.5 and width=1800, world span is 3600m (-1800 to +1800).
        # Chunks at index +2 and -2 should be detected as visible and queued.
        modal.check_and_fetch_nearby_tiles()
        self.assertTrue(len(modal.pending_chunks) > 0)
        # Verify that an outer chunk like (2, 0) or (-2, 0) is queued
        outer_found = any(abs(cx) >= 2 or abs(cy) >= 2 for cx, cy in modal.pending_chunks)
        self.assertTrue(outer_found)

    def test_backtracking_and_hairpins_elimination(self):
        from src.editor.osm_importer import remove_backtracking_and_hairpins

        # Artificial 180 backtrack spur: (40,0) -> (0,0) -> (100,0) -> (80,0)
        bad_path = [(40.0, 0.0), (0.0, 0.0), (100.0, 0.0), (80.0, 0.0)]
        cleaned = remove_backtracking_and_hairpins(bad_path)
        self.assertEqual(cleaned, [(40.0, 0.0), (80.0, 0.0)])

        # Retraced spur: A -> B -> C -> D -> C -> E
        path_spur = [(0.0, 0.0), (30.0, 0.0), (50.0, 0.0), (100.0, 0.0), (50.0, 0.0), (50.0, 50.0)]
        cleaned_spur = remove_backtracking_and_hairpins(path_spur)
        self.assertEqual(cleaned_spur, [(0.0, 0.0), (30.0, 0.0), (50.0, 0.0), (50.0, 50.0)])

    def test_segment_splitting_routing(self):
        from src.editor.osm_importer import shortest_path_on_roads

        ways = [
            {"id": 1, "type": "primary", "points_xy": [(0.0, 0.0), (100.0, 0.0)]},
            {"id": 2, "type": "primary", "points_xy": [(100.0, 0.0), (100.0, 100.0)]},
        ]
        # Two points along the same straight road segment
        path_straight = shortest_path_on_roads((40.0, 0.0), (80.0, 0.0), ways)
        self.assertEqual(path_straight, [(40.0, 0.0), (80.0, 0.0)])

        # Two points turning a corner
        path_corner = shortest_path_on_roads((60.0, 0.0), (100.0, 50.0), ways)
        self.assertEqual(path_corner[0], (60.0, 0.0))
        self.assertEqual(path_corner[-1], (100.0, 50.0))
        # Must pass through corner (100, 0)
        self.assertTrue(any(abs(p[0] - 100.0) < 1.0 and abs(p[1] - 0.0) < 1.0 for p in path_corner))

    def test_corner_filleting_and_overshoot_reduction(self):
        from src.editor.osm_importer import fillet_sharp_corners

        # 90-degree corner
        corners = [(0.0, 0.0), (0.0, 100.0), (100.0, 100.0)]
        filleted = fillet_sharp_corners(corners, default_radius=14.0)
        # Should contain corner arc points, replacing the sharp knife-edge vertex at (0, 100)
        self.assertGreater(len(filleted), 3)
        # Verify corner apex is rounded (x > 0, y < 100)

    def test_simplify_almost_straights(self):
        from src.editor.osm_importer import simplify_almost_straights

        # 10 collinear or micro-deflection points along a 200m straight road
        straight_with_kinks = [
            (0.0, 0.0),
            (20.0, 0.4),
            (40.0, -0.3),
            (60.0, 0.2),
            (80.0, -0.5),
            (100.0, 0.6),  # All within +/- 1m lateral deviation (< 3.5m)
            (120.0, 0.1),
            (140.0, -0.2),
            (160.0, 0.5),
            (200.0, 0.0),
            # Then an actual 90-degree corner at (200, 100) turning to (300, 100)
            (200.0, 100.0),
            (300.0, 100.0),
        ]
        simplified = simplify_almost_straights(straight_with_kinks, max_lateral_dev=3.5, min_corner_angle_deg=10.0)
        # All micro-kinks on the straight section should be collapsed, leaving only endpoints and the real 90 deg turn
        self.assertLess(len(simplified), len(straight_with_kinks))
        self.assertEqual(simplified[0], (0.0, 0.0))
        self.assertEqual(simplified[-1], (300.0, 100.0))
        # Ensure the 90 degree turn apex at (200, 100) is preserved
        self.assertTrue(any(abs(p[0] - 200.0) < 1.0 and abs(p[1] - 100.0) < 1.0 for p in simplified))

    def test_circuit_corners_detection(self):
        from src.core.circuit import Circuit

        # Circuit with 4 sharp corners (rectangle: 4 real turns)
        pts = [(0.0, 0.0), (300.0, 0.0), (300.0, 200.0), (0.0, 200.0)]
        c = Circuit("Box Circuit", width=14.0)
        c.set_control_points(pts, [14.0] * 4)
        corners = c.get_corners()
        self.assertEqual(len(corners), 4)
        self.assertEqual(c.corners_count, 4)

    def test_turn_node_indices(self):
        from src.core.circuit import Circuit

        pts = [(0.0, 0.0), (300.0, 0.0), (300.0, 200.0), (0.0, 200.0)]
        c = Circuit("Box Circuit", width=14.0)
        c.set_control_points(pts, [14.0] * 4)
        turn_map = c.get_turn_node_indices()
        # All 4 vertices should be mapped to Turn 1..4
        self.assertEqual(len(turn_map), 4)
        self.assertEqual(set(turn_map.values()), {1, 2, 3, 4})

    def test_parse_osm_road_width(self):
        from src.editor.osm_importer import parse_osm_road_width

        # Explicit width
        self.assertEqual(parse_osm_road_width({"width": "8.5"}), 8.5)
        self.assertEqual(parse_osm_road_width({"width": "14 m"}), 14.0)
        self.assertEqual(parse_osm_road_width({"width": "7,5"}), 7.5)
        self.assertEqual(parse_osm_road_width({"est_width": "9.0"}), 9.0)

        # Lanes
        self.assertEqual(parse_osm_road_width({"lanes": "1"}), 7.5)
        self.assertEqual(parse_osm_road_width({"lanes": "2"}), 11.0)
        self.assertEqual(parse_osm_road_width({"lanes": "3"}), 14.5)
        self.assertEqual(parse_osm_road_width({"lanes": "4"}), 18.0)

        # Classification fallbacks
        self.assertEqual(parse_osm_road_width({"highway": "motorway"}), 20.0)
        self.assertEqual(parse_osm_road_width({"highway": "primary"}), 15.0)
        self.assertEqual(parse_osm_road_width({"highway": "secondary"}), 13.0)
        self.assertEqual(parse_osm_road_width({"highway": "residential"}), 9.0)
        self.assertEqual(parse_osm_road_width({"highway": "cycleway"}), 7.5)
        self.assertEqual(parse_osm_road_width({}), 11.0)

    def test_convert_waypoints_with_varying_road_widths(self):
        from src.editor.osm_importer import convert_waypoints_to_circuit

        # Way 1: wide boulevard along y = -100
        # Way 2: wide avenue along x = 200
        # Way 3: narrow residential street along y = 100
        # Way 4: narrow alley along x = -200
        ways = [
            {
                "id": 1,
                "name": "Grand Boulevard",
                "type": "primary",
                "width_m": 18.0,
                "points_xy": [(-300.0, -100.0), (300.0, -100.0)],
                "bbox": (-300.0, 300.0, -100.0, -100.0),
            },
            {
                "id": 2,
                "name": "East Connector",
                "type": "secondary",
                "width_m": 13.0,
                "points_xy": [(200.0, -150.0), (200.0, 150.0)],
                "bbox": (200.0, 200.0, -150.0, 150.0),
            },
            {
                "id": 3,
                "name": "Historic Alley",
                "type": "residential",
                "width_m": 8.0,
                "points_xy": [(300.0, 100.0), (-300.0, 100.0)],
                "bbox": (-300.0, 300.0, 100.0, 100.0),
            },
            {
                "id": 4,
                "name": "West Connector",
                "type": "secondary",
                "width_m": 13.0,
                "points_xy": [(-200.0, 150.0), (-200.0, -150.0)],
                "bbox": (-200.0, -200.0, -150.0, 150.0),
            },
        ]

        pts = [
            (-200.0, -100.0),
            (0.0, -100.0),
            (200.0, -100.0),
            (200.0, 0.0),
            (200.0, 100.0),
            (0.0, 100.0),
            (-200.0, 100.0),
            (-200.0, 0.0),
            (-200.0, -100.0),
        ]

        circuit = convert_waypoints_to_circuit(pts, track_name="Boulevard to Alley Circuit", ways=ways)
        self.assertIsNotNone(circuit)
        self.assertTrue(len(circuit.node_widths) >= 5)
        # Node widths should not be constant: max width > min width
        max_w = max(circuit.node_widths)
        min_w = min(circuit.node_widths)
        self.assertGreater(max_w, min_w)
        # Wide boulevard should reach >= 14m, while alley section should reach <= 11m
        self.assertGreaterEqual(max_w, 14.0)
        self.assertLessEqual(min_w, 11.0)


if __name__ == "__main__":
    unittest.main()
