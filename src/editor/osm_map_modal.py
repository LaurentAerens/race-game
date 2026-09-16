"""
OSM Map Modal dialog for TrackEditor.
Allows users to search any real-world location, renders public roads from OpenStreetMap,
enables panning/zooming, clicking roads to place waypoints, auto-closing the loop,
and generating a valid Circuit directly in the Track Editor.
Zero hardcoded/trademarked presets.
"""

import math
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame

from src.core.circuit import Circuit
from src.editor.osm_importer import (
    convert_waypoints_to_circuit,
    fetch_road_network,
    geocode_location,
    remove_backtracking_and_hairpins,
    shortest_path_on_roads,
    snap_point_to_roads,
    unproject_meters_to_gps,
)

ROAD_COLORS = {
    "motorway": (230, 100, 100),
    "trunk": (240, 140, 80),
    "primary": (240, 200, 80),
    "secondary": (210, 220, 100),
    "tertiary": (180, 200, 180),
    "residential": (140, 160, 170),
    "unclassified": (130, 150, 160),
    "living_street": (150, 180, 190),
    "cycleway": (80, 220, 170),  # Vibrant teal-green for bike highways & cycleways
    "service": (110, 130, 140),
    "track": (170, 140, 100),
    "path": (90, 190, 160),
    "road": (120, 140, 150),
}

ROAD_WIDTHS = {
    "motorway": 5,
    "trunk": 4,
    "primary": 4,
    "secondary": 3,
    "tertiary": 2,
    "residential": 2,
    "unclassified": 2,
    "living_street": 2,
    "cycleway": 3,
    "service": 2,
    "track": 2,
    "path": 2,
    "road": 2,
}


class OSMMapModal:
    def __init__(self, on_circuit_created: Callable[[Circuit], None]):
        self.on_circuit_created = on_circuit_created
        self.is_open = False

        # Search query & text input
        self.search_query = ""
        self.search_active = False
        self.location_name = "No location loaded"
        self.status_message = "Type a city or district and press Enter to search."
        self.is_loading = False

        # Map data
        self.road_data: Optional[Dict[str, Any]] = None
        self.current_lat: float = 0.0
        self.current_lon: float = 0.0
        self.loaded_chunks: set = set()  # set of (chunk_x, chunk_y) tile indices in meters
        self.pending_chunks: set = set()  # set of (chunk_x, chunk_y) awaiting fetch
        self.is_fetching_chunk: bool = False
        self._tile_worker_thread: Optional[threading.Thread] = None

        # Viewport camera (meters to screen)
        self.cam_x: float = 0.0  # Center X in meters
        self.cam_y: float = 0.0  # Center Y in meters
        self.last_check_cam: Tuple[float, float] = (0.0, 0.0)
        self.zoom: float = 0.8  # pixels per meter (default 0.8 = ~1000m across viewport)
        self.is_panning: bool = False
        self.pan_start_screen: Tuple[int, int] = (0, 0)
        self.pan_start_cam: Tuple[float, float] = (0.0, 0.0)

        # Selected Waypoints (in meters, snapped to roads)
        self.waypoints: List[Tuple[float, float]] = []
        self.tracked_path: List[Tuple[float, float]] = []
        self.hovered_snap: Optional[Dict[str, Any]] = None

        # Fonts
        self.font_title = None
        self.font_ui = None
        self.font_bold = None
        self.font_small = None

        # UI Layout state
        self.modal_rect = pygame.Rect(0, 0, 0, 0)
        self.map_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_rects: Dict[str, pygame.Rect] = {}

    def _init_fonts(self):
        if self.font_title is None:
            self.font_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
            self.font_ui = pygame.font.SysFont("Segoe UI", 14)
            self.font_bold = pygame.font.SysFont("Segoe UI", 14, bold=True)
            self.font_small = pygame.font.SysFont("Segoe UI", 12)

    def open(self):
        self.is_open = True
        self.search_active = True
        self.search_query = ""
        self.status_message = "Type a city or location (e.g. Monaco, Austin, Melbourne) and press Enter."
        try:
            pygame.key.start_text_input()
        except Exception:
            # Older pygame versions or platforms without IME/text input support
            pass

    def close(self):
        self.is_open = False
        self.search_active = False
        try:
            pygame.key.stop_text_input()
        except Exception:
            # Older pygame versions or platforms without IME/text input support
            pass

    def screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        """Convert screen pixel coordinate inside map_rect to world meters."""
        cx = self.map_rect.centerx
        cy = self.map_rect.centery
        wx = self.cam_x + (sx - cx) / self.zoom
        wy = self.cam_y + (sy - cy) / self.zoom
        return (wx, wy)

    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        """Convert world meters to screen pixel coordinate."""
        cx = self.map_rect.centerx
        cy = self.map_rect.centery
        sx = int(cx + (wx - self.cam_x) * self.zoom)
        sy = int(cy + (wy - self.cam_y) * self.zoom)
        return (sx, sy)

    def trigger_search(self):
        query = self.search_query.strip()
        if not query or self.is_loading:
            return

        self.is_loading = True
        self.status_message = f"Searching for '{query}'..."
        self.search_active = False

        def _worker():
            try:
                loc = geocode_location(query)
                if not loc:
                    self.status_message = f"Location '{query}' not found. Try another city or district."
                    self.is_loading = False
                    return

                self.status_message = f"Found '{loc['display_name'][:50]}...'. Fetching roads from OpenStreetMap..."
                self.location_name = loc["display_name"]
                self.current_lat = loc["lat"]
                self.current_lon = loc["lon"]

                roads = fetch_road_network(self.current_lat, self.current_lon, radius_m=3000)
                self.road_data = roads
                self.cam_x = 0.0
                self.cam_y = 0.0
                self.last_check_cam = (0.0, 0.0)
                self.zoom = 0.6
                self.waypoints.clear()
                self.tracked_path.clear()
                self.pending_chunks.clear()
                # Mark origin and immediately adjacent grid tiles as covered by the large 3000m initial fetch
                self.loaded_chunks = {(0, 0), (-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)}
                total_ways = len(roads.get("ways", []))
                if total_ways > 0:
                    self.status_message = (
                        f"Loaded {total_ways} roads and paths. Pan anywhere to automatically load more!"
                    )
                else:
                    self.status_message = "No roads found in this area. Try another location."

                # Check visible viewport immediately to fetch any outer visible tiles
                self.check_and_fetch_nearby_tiles()
            except Exception as ex:
                self.status_message = f"Error fetching map: {ex}"
            finally:
                self.is_loading = False

        threading.Thread(target=_worker, daemon=True).start()

    def check_and_fetch_nearby_tiles(self):
        """Identifies any unloaded chunks within or bordering the visible viewport and queues them."""
        if not self.current_lat or not self.current_lon or self.is_loading:
            return

        chunk_size_m = 1600.0

        # Determine visible world coordinates. Fall back to estimated screen size if map_rect isn't laid out yet.
        if self.map_rect.width > 0 and self.map_rect.height > 0:
            left_wx, top_wy = self.screen_to_world(self.map_rect.left, self.map_rect.top)
            right_wx, bottom_wy = self.screen_to_world(self.map_rect.right, self.map_rect.bottom)
            min_wx = min(left_wx, right_wx)
            max_wx = max(left_wx, right_wx)
            min_wy = min(top_wy, bottom_wy)
            max_wy = max(top_wy, bottom_wy)
        else:
            span_x = 1800.0 / self.zoom / 2.0
            span_y = 900.0 / self.zoom / 2.0
            min_wx = self.cam_x - span_x
            max_wx = self.cam_x + span_x
            min_wy = self.cam_y - span_y
            max_wy = self.cam_y + span_y

        # Include 1 chunk buffer around visible area for seamless prefetching
        min_cx = int(math.floor(min_wx / chunk_size_m)) - 1
        max_cx = int(math.ceil(max_wx / chunk_size_m)) + 1
        min_cy = int(math.floor(min_wy / chunk_size_m)) - 1
        max_cy = int(math.ceil(max_wy / chunk_size_m)) + 1

        needed = []
        for cy in range(min_cy, max_cy + 1):
            for cx in range(min_cx, max_cx + 1):
                key = (cx, cy)
                if key not in self.loaded_chunks and key not in self.pending_chunks:
                    dist_sq = (cx * chunk_size_m - self.cam_x) ** 2 + (cy * chunk_size_m - self.cam_y) ** 2
                    needed.append((dist_sq, key))

        if not needed:
            return

        # Prioritize chunks closest to current camera center
        needed.sort(key=lambda item: item[0])
        for _, key in needed[:16]:
            self.pending_chunks.add(key)

        self._ensure_worker_running()

    def _ensure_worker_running(self):
        if self._tile_worker_thread is not None and self._tile_worker_thread.is_alive():
            return
        self._tile_worker_thread = threading.Thread(target=self._tile_worker_loop, daemon=True)
        self._tile_worker_thread.start()

    def _tile_worker_loop(self):
        chunk_size_m = 1600.0
        while self.pending_chunks:
            # Pick chunk closest to camera center's latest position
            cur_cam_x, cur_cam_y = self.cam_x, self.cam_y
            best_chunk = None
            best_dist = float("inf")
            for chunk in list(self.pending_chunks):
                d = (chunk[0] * chunk_size_m - cur_cam_x) ** 2 + (chunk[1] * chunk_size_m - cur_cam_y) ** 2
                if d < best_dist:
                    best_dist = d
                    best_chunk = chunk

            if not best_chunk:
                break

            self.pending_chunks.discard(best_chunk)
            cx_idx, cy_idx = best_chunk

            if best_chunk in self.loaded_chunks:
                continue

            self.loaded_chunks.add(best_chunk)
            self.is_fetching_chunk = True

            target_wx = cx_idx * chunk_size_m
            target_wy = cy_idx * chunk_size_m
            target_lat, target_lon = unproject_meters_to_gps(target_wx, target_wy, self.current_lat, self.current_lon)
            rem = len(self.pending_chunks)
            if rem > 0:
                self.status_message = f"Auto-loading road area ({cx_idx:+d}, {cy_idx:+d}) [{rem} queued]..."
            else:
                self.status_message = f"Auto-loading road area ({cx_idx:+d}, {cy_idx:+d})..."

            try:
                new_chunk = fetch_road_network(
                    target_lat, target_lon, radius_m=2400, origin_lat=self.current_lat, origin_lon=self.current_lon
                )
                new_ways = new_chunk.get("ways", [])
                if self.road_data and "ways" in self.road_data:
                    existing_ids = {w["id"] for w in self.road_data["ways"]}
                    added_ways = [w for w in new_ways if w["id"] not in existing_ids]
                    if added_ways:
                        # Atomic list replacement prevents race conditions with renderer
                        self.road_data["ways"] = self.road_data["ways"] + added_ways
                    total_all = len(self.road_data["ways"])
                    if len(self.pending_chunks) == 0:
                        self.status_message = f"All visible roads loaded ({total_all} total). Pan anywhere freely!"
            except Exception as e:
                print(f"[OSMMapModal] Chunk auto-load error for {best_chunk}: {e}")
            finally:
                self.is_fetching_chunk = False

            # Modest delay between consecutive uncached requests to avoid Overpass rate limit
            time.sleep(0.05)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if the event was consumed by the modal."""
        if not self.is_open:
            return False

        # Text entry via Pygame TEXTINPUT (standard in SDL2/pygame-ce)
        if event.type == pygame.TEXTINPUT and self.search_active:
            if event.text:
                self.search_query += event.text
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True

            if self.search_active:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    self.trigger_search()
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.search_query = self.search_query[:-1]
                    return True
                # Note: Printable characters are handled exclusively by pygame.TEXTINPUT
                # to prevent double typing on systems that emit both KEYDOWN and TEXTINPUT.
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Handle search bar click
            search_bar_rect = self.btn_rects.get("search_bar")
            if search_bar_rect and search_bar_rect.collidepoint(mx, my):
                self.search_active = True
                try:
                    pygame.key.start_text_input()
                except Exception:
                    # Ignore if platform doesn't support text input API
                    pass
                return True
            else:
                self.search_active = False

            # Handle UI buttons
            for btn_name, rect in self.btn_rects.items():
                if btn_name != "search_bar" and rect.collidepoint(mx, my):
                    self._on_button_clicked(btn_name)
                    return True

            # Handle map interaction
            if self.map_rect.collidepoint(mx, my):
                if event.button == 1:  # Left click: place or snap waypoint
                    new_pt = (
                        self.hovered_snap["snapped_xy"]
                        if self.hovered_snap
                        else (round(self.screen_to_world(mx, my)[0], 2), round(self.screen_to_world(mx, my)[1], 2))
                    )
                    self.waypoints.append(new_pt)

                    # Route along road network from previous waypoint to new waypoint
                    if len(self.waypoints) == 1:
                        self.tracked_path = [new_pt]
                    else:
                        prev_pt = self.waypoints[-2]
                        ways = self.road_data.get("ways", []) if self.road_data else []
                        sub_path = shortest_path_on_roads(prev_pt, new_pt, ways)
                        # Append new sub-path avoiding immediate duplicates
                        for p in sub_path[1:]:
                            self.tracked_path.append(p)
                        self.tracked_path = remove_backtracking_and_hairpins(self.tracked_path)

                    w_info = (
                        f" ({self.hovered_snap.get('width_m', 12.0):.1f}m width)"
                        if (self.hovered_snap and "width_m" in self.hovered_snap)
                        else ""
                    )
                    road_label = f" on {self.hovered_snap['road_name']}{w_info}" if self.hovered_snap else ""
                    self.status_message = (
                        f"Added waypoint #{len(self.waypoints)}{road_label} (Track follows road network)."
                    )
                    return True

                elif event.button == 3:  # Right click: start pan
                    self.is_panning = True
                    self.pan_start_screen = (mx, my)
                    self.pan_start_cam = (self.cam_x, self.cam_y)
                    return True

                elif event.button == 4:  # Scroll up: zoom in
                    self.zoom = min(5.0, self.zoom * 1.15)
                    self.check_and_fetch_nearby_tiles()
                    return True

                elif event.button == 5:  # Scroll down: zoom out
                    self.zoom = max(0.20, self.zoom / 1.15)
                    self.check_and_fetch_nearby_tiles()
                    return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self.is_panning = False
                self.last_check_cam = (self.cam_x, self.cam_y)
                self.check_and_fetch_nearby_tiles()
                return True

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.is_panning:
                dx = (mx - self.pan_start_screen[0]) / self.zoom
                dy = (my - self.pan_start_screen[1]) / self.zoom
                self.cam_x = self.pan_start_cam[0] - dx
                self.cam_y = self.pan_start_cam[1] - dy

                # Stream tiles smoothly while panning every ~200m
                dist_moved = math.hypot(self.cam_x - self.last_check_cam[0], self.cam_y - self.last_check_cam[1])
                if dist_moved > 200.0:
                    self.last_check_cam = (self.cam_x, self.cam_y)
                    self.check_and_fetch_nearby_tiles()
                return True

            # Road hover snapping
            if self.map_rect.collidepoint(mx, my) and self.road_data:
                wx, wy = self.screen_to_world(mx, my)
                snap_radius_m = 60.0 / max(0.1, self.zoom)  # screen tolerance converted to meters
                snap_res = snap_point_to_roads(
                    wx, wy, self.road_data.get("ways", []), max_dist=max(20.0, snap_radius_m)
                )
                self.hovered_snap = snap_res
                return True
            else:
                self.hovered_snap = None

        return True  # Consume all events while modal is open

    def _on_button_clicked(self, name: str):
        if name == "search":
            self.trigger_search()
        elif name == "close":
            self.close()
        elif name == "clear":
            self.waypoints.clear()
            self.tracked_path.clear()
            self.status_message = "Waypoints cleared."
        elif name == "undo":
            if self.waypoints:
                self.waypoints.pop()
                # Reconstruct tracked_path along roads for remaining waypoints
                self.tracked_path = []
                ways = self.road_data.get("ways", []) if self.road_data else []
                for idx, pt in enumerate(self.waypoints):
                    if idx == 0:
                        self.tracked_path = [pt]
                    else:
                        sub = shortest_path_on_roads(self.waypoints[idx - 1], pt, ways)
                        for p in sub[1:]:
                            self.tracked_path.append(p)
                self.tracked_path = remove_backtracking_and_hairpins(self.tracked_path)
                self.status_message = f"Removed last waypoint ({len(self.waypoints)} remaining)."
        elif name == "auto_close":
            if len(self.waypoints) >= 3:
                start_pt = self.waypoints[0]
                last_pt = self.waypoints[-1]
                self.waypoints.append(start_pt)
                ways = self.road_data.get("ways", []) if self.road_data else []
                sub = shortest_path_on_roads(last_pt, start_pt, ways)
                for p in sub[1:]:
                    self.tracked_path.append(p)
                self.tracked_path = remove_backtracking_and_hairpins(self.tracked_path)
                self.status_message = "Closed circuit loop along public road network."
        elif name == "convert":
            track_pts = self.tracked_path if len(self.tracked_path) >= 5 else self.waypoints
            if len(track_pts) < 4:
                self.status_message = "Need at least 4 waypoints to form a circuit."
                return

            circuit_name = self.location_name.split(",")[0].strip() if self.location_name else "Street Circuit"
            ways = self.road_data.get("ways", []) if self.road_data else None
            circuit = convert_waypoints_to_circuit(track_pts, track_name=circuit_name, ways=ways)
            if circuit:
                self.on_circuit_created(circuit)
                self.close()
            else:
                self.status_message = "Failed to create circuit: check that loop is not intersecting or too small."

    def render(self, screen: pygame.Surface):
        if not self.is_open:
            return

        self._init_fonts()
        sw, sh = screen.get_size()

        # Dim background
        dim_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim_surface.fill((0, 0, 0, 180))
        screen.blit(dim_surface, (0, 0))

        # Main modal window (leave 40px margin)
        mw = max(800, sw - 80)
        mh = max(500, sh - 80)
        mx = (sw - mw) // 2
        my = (sh - mh) // 2
        self.modal_rect = pygame.Rect(mx, my, mw, mh)

        # Draw modal frame
        pygame.draw.rect(screen, (24, 26, 32), self.modal_rect, border_radius=8)
        pygame.draw.rect(screen, (60, 70, 85), self.modal_rect, width=2, border_radius=8)

        # Header bar (46px)
        header_rect = pygame.Rect(mx, my, mw, 46)
        pygame.draw.rect(screen, (32, 35, 44), header_rect, border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.line(screen, (50, 58, 70), (mx, my + 46), (mx + mw, my + 46), 1)

        title_surf = self.font_title.render("REAL-WORLD ROAD MAP IMPORTER (OPENSTREETMAP)", True, (240, 240, 240))
        screen.blit(title_surf, (mx + 16, my + 12))

        # Close button (top right)
        close_btn_rect = pygame.Rect(mx + mw - 38, my + 8, 30, 30)
        self.btn_rects["close"] = close_btn_rect
        pygame.draw.rect(screen, (180, 50, 50), close_btn_rect, border_radius=4)
        x_surf = self.font_bold.render("X", True, (255, 255, 255))
        screen.blit(x_surf, x_surf.get_rect(center=close_btn_rect.center))

        # Search bar row (below header)
        search_y = my + 54
        lbl_search = self.font_bold.render("Search City / Location:", True, (200, 210, 225))
        screen.blit(lbl_search, (mx + 16, search_y + 4))

        search_x = mx + 180
        search_w = mw - 340
        search_box = pygame.Rect(search_x, search_y, search_w, 32)
        self.btn_rects["search_bar"] = search_box

        box_border_color = (0, 168, 255) if self.search_active else (70, 80, 95)
        pygame.draw.rect(screen, (15, 17, 22), search_box, border_radius=4)
        pygame.draw.rect(screen, box_border_color, search_box, width=2, border_radius=4)

        display_text = (
            self.search_query
            if self.search_query
            else ("Type city name (e.g. Monaco, Austin, Melbourne)..." if not self.search_active else "")
        )
        text_color = (255, 255, 255) if self.search_query else (120, 130, 145)
        query_surf = self.font_ui.render(display_text, True, text_color)
        screen.blit(query_surf, (search_x + 8, search_y + 6))

        # Blinking cursor when active
        if self.search_active:
            cursor_x = search_x + 8 + (query_surf.get_width() if self.search_query else 0)
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                pygame.draw.line(screen, (0, 200, 255), (cursor_x + 2, search_y + 7), (cursor_x + 2, search_y + 25), 2)

        # Search button
        btn_search = pygame.Rect(search_x + search_w + 8, search_y, 110, 32)
        self.btn_rects["search"] = btn_search
        search_btn_col = (0, 120, 215) if not self.is_loading else (60, 70, 85)
        pygame.draw.rect(screen, search_btn_col, btn_search, border_radius=4)
        btn_search_txt = self.font_bold.render("SEARCH" if not self.is_loading else "LOADING...", True, (255, 255, 255))
        screen.blit(btn_search_txt, btn_search_txt.get_rect(center=btn_search.center))

        # Map viewport
        map_y = search_y + 40
        map_h = mh - 146
        map_w = mw - 32
        self.map_rect = pygame.Rect(mx + 16, map_y, map_w, map_h)

        # Draw map background
        pygame.draw.rect(screen, (16, 20, 25), self.map_rect)
        pygame.draw.rect(screen, (45, 55, 68), self.map_rect, width=1)

        # Clip rendering to map_rect
        clip_prev = screen.get_clip()
        screen.set_clip(self.map_rect)

        # Render roads
        if self.road_data and "ways" in self.road_data:
            self._render_roads(screen)
        elif self.is_loading:
            loading_txt = self.font_title.render("FETCHING PUBLIC ROADS FROM OPENSTREETMAP...", True, (0, 200, 255))
            screen.blit(loading_txt, loading_txt.get_rect(center=self.map_rect.center))
        else:
            hint_empty = self.font_ui.render("Search a city above to load road network.", True, (90, 105, 125))
            screen.blit(hint_empty, hint_empty.get_rect(center=self.map_rect.center))

        # Render Waypoints and connecting track
        self._render_waypoints(screen)

        # Render snapped hover indicator
        if self.hovered_snap:
            pt = self.hovered_snap["snapped_xy"]
            sx, sy = self.world_to_screen(pt[0], pt[1])
            pygame.draw.circle(screen, (0, 255, 255), (sx, sy), 6, 2)
            w_str = f", {self.hovered_snap['width_m']:.1f}m" if "width_m" in self.hovered_snap else ""
            lbl = self.font_small.render(
                f"{self.hovered_snap['road_name']} ({self.hovered_snap['road_type']}{w_str})", True, (0, 255, 255)
            )
            screen.blit(lbl, (sx + 10, sy - 10))

        # Reset clip
        screen.set_clip(clip_prev)

        # Bottom Action Bar
        bottom_y = my + mh - 44
        action_x = mx + 16

        # Action Buttons
        btn_clear = pygame.Rect(action_x, bottom_y, 80, 32)
        self.btn_rects["clear"] = btn_clear
        pygame.draw.rect(screen, (60, 65, 75), btn_clear, border_radius=4)
        lbl_clr = self.font_ui.render("CLEAR", True, (220, 220, 220))
        screen.blit(lbl_clr, lbl_clr.get_rect(center=btn_clear.center))

        btn_undo = pygame.Rect(action_x + 90, bottom_y, 80, 32)
        self.btn_rects["undo"] = btn_undo
        pygame.draw.rect(screen, (60, 65, 75), btn_undo, border_radius=4)
        lbl_undo = self.font_ui.render("UNDO", True, (220, 220, 220))
        screen.blit(lbl_undo, lbl_undo.get_rect(center=btn_undo.center))

        btn_auto = pygame.Rect(action_x + 180, bottom_y, 140, 32)
        self.btn_rects["auto_close"] = btn_auto
        pygame.draw.rect(screen, (38, 110, 160), btn_auto, border_radius=4)
        lbl_auto = self.font_ui.render("AUTO-CLOSE LOOP", True, (255, 255, 255))
        screen.blit(lbl_auto, lbl_auto.get_rect(center=btn_auto.center))

        btn_convert = pygame.Rect(action_x + 330, bottom_y, 180, 32)
        self.btn_rects["convert"] = btn_convert
        convert_col = (46, 139, 87) if len(self.waypoints) >= 4 else (60, 70, 75)
        pygame.draw.rect(screen, convert_col, btn_convert, border_radius=4)
        lbl_conv = self.font_bold.render("CONVERT TO TRACK", True, (255, 255, 255))
        screen.blit(lbl_conv, lbl_conv.get_rect(center=btn_convert.center))

        # Status & Instructions on right
        status_x = action_x + 520
        status_col = (
            (255, 120, 120)
            if "not found" in self.status_message.lower() or "error" in self.status_message.lower()
            else (200, 215, 230)
        )
        status_surf = self.font_small.render(self.status_message, True, status_col)
        screen.blit(status_surf, (status_x, bottom_y + 8))

        # Map controls helper hint (overlay top right inside map)
        hint_surf = self.font_small.render(
            "Right-Click Drag: Pan  |  Scroll: Zoom  |  Left-Click Road: Place Waypoint", True, (160, 180, 200)
        )
        hint_bg = pygame.Rect(
            self.map_rect.right - hint_surf.get_width() - 14, self.map_rect.top + 6, hint_surf.get_width() + 10, 20
        )
        pygame.draw.rect(screen, (20, 24, 30), hint_bg, border_radius=3)
        screen.blit(hint_surf, (hint_bg.x + 5, hint_bg.y + 2))

    def _render_roads(self, screen: pygame.Surface):
        ways = self.road_data.get("ways", [])
        if not ways:
            return

        left_wx, top_wy = self.screen_to_world(self.map_rect.left, self.map_rect.top)
        right_wx, bottom_wy = self.screen_to_world(self.map_rect.right, self.map_rect.bottom)
        min_wx = min(left_wx, right_wx)
        max_wx = max(left_wx, right_wx)
        min_wy = min(top_wy, bottom_wy)
        max_wy = max(top_wy, bottom_wy)

        for way in ways:
            pts = way.get("points_xy", [])
            if len(pts) < 2:
                continue

            bbox = way.get("bbox")
            if bbox:
                w_min_x, w_max_x, w_min_y, w_max_y = bbox
                if w_max_x < min_wx or w_min_x > max_wx or w_max_y < min_wy or w_min_y > max_wy:
                    continue

            road_type = way.get("type", "road")
            color = ROAD_COLORS.get(road_type, (130, 140, 150))
            width_m = way.get("width_m")
            if width_m is not None:
                base_w = max(1.5, width_m * 0.25)
            else:
                base_w = ROAD_WIDTHS.get(road_type, 2)
            screen_w = max(1, int(base_w * self.zoom * 0.8))

            screen_pts = [self.world_to_screen(p[0], p[1]) for p in pts]

            if not bbox:
                min_x = min(p[0] for p in screen_pts)
                max_x = max(p[0] for p in screen_pts)
                min_y = min(p[1] for p in screen_pts)
                max_y = max(p[1] for p in screen_pts)
                if (
                    max_x < self.map_rect.left
                    or min_x > self.map_rect.right
                    or max_y < self.map_rect.top
                    or min_y > self.map_rect.bottom
                ):
                    continue

            if len(screen_pts) >= 2:
                pygame.draw.lines(screen, color, False, screen_pts, screen_w)

    def _render_waypoints(self, screen: pygame.Surface):
        if not self.waypoints:
            return

        screen_pts = [self.world_to_screen(p[0], p[1]) for p in self.waypoints]

        # Draw connecting line ribbon along tracked road path
        path_to_draw = self.tracked_path if len(self.tracked_path) >= 2 else self.waypoints
        if len(path_to_draw) >= 2:
            ribbon_screen_pts = [self.world_to_screen(p[0], p[1]) for p in path_to_draw]
            pygame.draw.lines(screen, (255, 200, 0), False, ribbon_screen_pts, 3)

        # Draw dots
        for idx, sp in enumerate(screen_pts):
            is_first = idx == 0
            col = (50, 255, 50) if is_first else (0, 220, 255)
            r = 6 if is_first else 5
            pygame.draw.circle(screen, col, sp, r)
            pygame.draw.circle(screen, (0, 0, 0), sp, r, 1)

            # Node number label
            num_surf = self.font_small.render(str(idx + 1), True, (255, 255, 255))
            screen.blit(num_surf, (sp[0] + 7, sp[1] - 8))
