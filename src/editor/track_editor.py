import math
import os
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from ..core.circuit import Circuit
from ..core.tires import TIRE_COMPOUNDS
from ..render.camera import Camera
from ..render.track_renderer import TrackRenderer
from ..ui.theme import UITheme
from .load_track_modal import LoadTrackModal
from .osm_map_modal import OSMMapModal

DRY_COMPOUND_KEYS = ["HARD", "MEDIUM", "SOFT", "SUPERSOFT", "HYPERSOFT"]
DRY_COMPOUND_TIERS = ["C1", "C2", "C3", "C4", "C5"]


class TrackEditor:
    """
    Robust Interactive CAD-style Circuit Designer.
    Create, drag, reshape corners, adjust per-section / per-node track width,
    place DRS zones, design pit lane (entry, exit, side, offset),
    mouse-wheel zoom, pan canvas, pick free 3-compound tyre allocations,
    save/load tracks and race on them.
    """

    def __init__(self, screen_width: int, screen_height: int, on_test_race: Callable[[Circuit], None]):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.on_test_race = on_test_race

        self.circuit = Circuit(name="My Custom Circuit", width=14.0)
        self.track_renderer = TrackRenderer()
        self.camera = Camera(screen_width, screen_height)
        self.osm_modal = OSMMapModal(on_circuit_created=self.on_osm_circuit_loaded)
        self.load_modal = LoadTrackModal(on_track_loaded=self.on_track_loaded)

        self.view_rect = pygame.Rect(280, 50, screen_width - 290, screen_height - 60)
        self.panel_rect = pygame.Rect(10, 50, 260, screen_height - 60)

        # Editor State
        self.selected_node_a: Optional[int] = 0
        self.selected_node_b: Optional[int] = 2
        self.is_dragging: bool = False
        self.is_panning: bool = False
        self.pan_start: Tuple[int, int] = (0, 0)
        self.hovered_node_idx: Optional[int] = None
        self._drag_start_state: Optional[dict] = None

        # Undo / Redo History
        self.undo_stack: List[dict] = []
        self.redo_stack: List[dict] = []

        self.status_message: str = (
            "Left-click: Drag/Insert • Right-click/Del: Remove Point • Ctrl+Z: Undo • Scroll: Zoom"
        )
        self._init_fonts()
        self._init_template()

    def _get_state_snapshot(self) -> dict:
        return {
            "control_points": list(self.circuit.control_points),
            "node_widths": list(self.circuit.node_widths),
            "drs_zones": [dict(z) for z in self.circuit.drs_zones],
            "pit_entry_node": self.circuit.pit_entry_node,
            "pit_exit_node": self.circuit.pit_exit_node,
            "pit_side": self.circuit.pit_side,
            "pit_offset_m": self.circuit.pit_offset_m,
            "nominated_compounds": list(self.circuit.nominated_compounds),
            "selected_node_a": self.selected_node_a,
            "selected_node_b": self.selected_node_b,
        }

    def _restore_state_snapshot(self, state: dict):
        self.circuit.control_points = list(state["control_points"])
        self.circuit.node_widths = list(state["node_widths"])
        self.circuit.drs_zones = [dict(z) for z in state["drs_zones"]]
        self.circuit.pit_entry_node = state["pit_entry_node"]
        self.circuit.pit_exit_node = state["pit_exit_node"]
        self.circuit.pit_side = state["pit_side"]
        self.circuit.pit_offset_m = state["pit_offset_m"]
        self.circuit.nominated_compounds = list(state["nominated_compounds"])
        self.selected_node_a = state["selected_node_a"]
        self.selected_node_b = state["selected_node_b"]
        if self.selected_node_a is not None and self.selected_node_a >= len(self.circuit.control_points):
            self.selected_node_a = max(0, len(self.circuit.control_points) - 1)
        if self.selected_node_b is not None and self.selected_node_b >= len(self.circuit.control_points):
            self.selected_node_b = max(0, len(self.circuit.control_points) - 1)
        self.circuit.build_circuit()

    def _push_undo(self, state: Optional[dict] = None):
        snapshot = state if state is not None else self._get_state_snapshot()
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            self.status_message = "Nothing to undo."
            return

        current_state = self._get_state_snapshot()
        self.redo_stack.append(current_state)
        prev_state = self.undo_stack.pop()
        self._restore_state_snapshot(prev_state)
        self.status_message = f"Undid action ({len(self.undo_stack)} undo steps remaining)."

    def redo(self):
        if not self.redo_stack:
            self.status_message = "Nothing to redo."
            return

        current_state = self._get_state_snapshot()
        self.undo_stack.append(current_state)
        next_state = self.redo_stack.pop()
        self._restore_state_snapshot(next_state)
        self.status_message = f"Redid action ({len(self.redo_stack)} redo steps remaining)."

    def delete_selected_node(self):
        if self.selected_node_a is None:
            self.status_message = "No point selected to remove. Left-click a point first."
            return

        idx = self.selected_node_a
        if idx < 0 or idx >= len(self.circuit.control_points):
            return

        if len(self.circuit.control_points) <= 3:
            self.status_message = "Cannot remove point: Circuit requires at least 3 control points."
            return

        self._push_undo()
        del self.circuit.control_points[idx]
        if idx < len(self.circuit.node_widths):
            del self.circuit.node_widths[idx]

        # Fix pit lane endpoints if they pointed to deleted node
        if self.circuit.pit_entry_node is not None:
            if self.circuit.pit_entry_node == idx:
                self.circuit.pit_entry_node = max(0, idx - 1)
            elif self.circuit.pit_entry_node > idx:
                self.circuit.pit_entry_node -= 1

        if self.circuit.pit_exit_node is not None:
            if self.circuit.pit_exit_node == idx:
                self.circuit.pit_exit_node = min(len(self.circuit.control_points) - 1, idx)
            elif self.circuit.pit_exit_node > idx:
                self.circuit.pit_exit_node -= 1

        # Fix DRS zones
        valid_drs = []
        for zone in self.circuit.drs_zones:
            za = zone["node_a"]
            zb = zone["node_b"]
            if za == idx or zb == idx:
                continue
            if za > idx:
                zone["node_a"] = za - 1
            if zb > idx:
                zone["node_b"] = zb - 1
            valid_drs.append(zone)
        self.circuit.drs_zones = valid_drs

        self.circuit.build_circuit()
        self.selected_node_a = min(idx, len(self.circuit.control_points) - 1)
        if self.selected_node_b is not None and self.selected_node_b >= len(self.circuit.control_points):
            self.selected_node_b = max(0, len(self.circuit.control_points) - 1)

        self.status_message = f"Removed Point #{idx + 1} ({len(self.circuit.control_points)} points remaining)."

    def on_osm_circuit_loaded(self, new_circuit: Circuit):
        """Callback when an OpenStreetMap circuit has been generated."""
        self._push_undo()
        self.circuit = new_circuit
        self.selected_node_a = 0
        self.selected_node_b = 2 if len(new_circuit.control_points) > 2 else 0
        self.camera.fit_circuit(self.circuit, self.view_rect)
        self.camera.x = self.camera.overview_x
        self.camera.y = self.camera.overview_y
        self.camera.zoom = self.camera.overview_zoom
        self.camera.target_x = self.camera.overview_x
        self.camera.target_y = self.camera.overview_y
        self.camera.target_zoom = self.camera.overview_zoom
        self.status_message = f"Imported '{new_circuit.name}' ({new_circuit.length:.0f}m, {new_circuit.corners_count} Turns) from OpenStreetMap!"

    def on_track_loaded(self, new_circuit: Circuit):
        """Callback when a saved circuit JSON has been selected and loaded."""
        self._push_undo()
        self.circuit = new_circuit
        self.selected_node_a = 0
        self.selected_node_b = 2 if len(new_circuit.control_points) > 2 else 0
        self.camera.fit_circuit(self.circuit, self.view_rect)
        self.camera.x = self.camera.overview_x
        self.camera.y = self.camera.overview_y
        self.camera.zoom = self.camera.overview_zoom
        self.camera.target_x = self.camera.overview_x
        self.camera.target_y = self.camera.overview_y
        self.camera.target_zoom = self.camera.overview_zoom
        self.status_message = (
            f"Loaded track '{new_circuit.name}' ({new_circuit.length:.0f}m, {new_circuit.corners_count} Turns)!"
        )

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_btn = UITheme.get_font(12, bold=True)
        self.font_desc = UITheme.get_font(11, bold=False)
        self.font_badge = UITheme.get_font(11, bold=True)

    def resize(self, screen_width: int, screen_height: int):
        """Updates canvas and layout rects on window resize while preserving circuit state."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.camera.screen_width = screen_width
        self.camera.screen_height = screen_height
        self.view_rect = pygame.Rect(280, 50, screen_width - 290, screen_height - 60)
        self.panel_rect = pygame.Rect(10, 50, 260, screen_height - 60)
        self._init_fonts()

    def _init_template(self):
        pts = [(-250, -150), (0, -160), (250, -150), (350, 0), (250, 150), (0, 160), (-250, 150), (-350, 0)]
        widths = [16.0, 16.0, 15.0, 12.0, 11.0, 13.0, 14.0, 15.0]
        self.circuit.set_control_points(pts, widths)
        self.circuit.nominated_compounds = ["HARD", "SOFT", "SUPERSOFT"]
        self.circuit.set_pit_lane_endpoints(entry_node=7, exit_node=1, side="INSIDE", offset_m=14.0)
        self.selected_node_a = 0
        self.selected_node_b = 2
        self.add_drs_between_nodes(0, 2)
        self.camera.fit_circuit(self.circuit, self.view_rect)

    def _get_panel_buttons(self) -> Dict[str, pygame.Rect]:
        """Returns deterministic, perfectly spaced button bounding boxes with zero overlap."""
        px = self.panel_rect.x + 10
        pw = self.panel_rect.width - 20
        py = self.panel_rect.y

        btns = {
            # Row 1: Undo / Redo / Delete Point
            "undo": pygame.Rect(px, py + 70, 68, 22),
            "redo": pygame.Rect(px + 73, py + 70, 68, 22),
            "delete_node": pygame.Rect(px + 146, py + 70, pw - 146, 22),
            # Row 2: Camera View & Zoom
            "fit": pygame.Rect(px, py + 96, 96, 22),
            "zoom_in": pygame.Rect(px + 101, py + 96, 67, 22),
            "zoom_out": pygame.Rect(px + 173, py + 96, 67, 22),
            # Row 3 & 4: Width adjustments
            "width_plus": pygame.Rect(px, py + 122, 115, 24),
            "width_minus": pygame.Rect(px + 125, py + 122, 115, 24),
            "span_width": pygame.Rect(px, py + 150, 115, 22),
            "all_width": pygame.Rect(px + 125, py + 150, 115, 22),
            # Row 5: DRS
            "add_drs": pygame.Rect(px, py + 176, pw, 24),
            "clear_drs": pygame.Rect(px, py + 248, pw, 20),
            # Pit Lane Buttons
            "set_pit_in": pygame.Rect(px, py + 288, 115, 24),
            "set_pit_out": pygame.Rect(px + 125, py + 288, 115, 24),
            "toggle_pit_side": pygame.Rect(px, py + 316, 115, 24),
            "cycle_pit_offset": pygame.Rect(px + 125, py + 316, 115, 24),
            # File Actions
            "save_json": pygame.Rect(px, py + 388, 115, 24),
            "load_json": pygame.Rect(px + 125, py + 388, 115, 24),
            "import_osm": pygame.Rect(px, py + 416, 115, 24),
            "reset_track": pygame.Rect(px + 125, py + 416, 115, 24),
            "add_to_calendar": pygame.Rect(px, py + 444, pw, 24),
            "race_now": pygame.Rect(px, py + 472, pw, 34),
        }
        return btns

    def _get_compound_chip_rects(self) -> List[Tuple[str, str, pygame.Rect]]:
        """Returns rects for C1, C2, C3, C4, C5 selector chips."""
        px = self.panel_rect.x + 10
        py = self.panel_rect.y + 358
        chip_w = 44
        gap = 5
        rects = []
        for idx, (c_key, tier) in enumerate(zip(DRY_COMPOUND_KEYS, DRY_COMPOUND_TIERS)):
            r = pygame.Rect(px + idx * (chip_w + gap), py, chip_w, 24)
            rects.append((c_key, tier, r))
        return rects

    def handle_event(self, event: pygame.event.Event):
        # 0. Modal dialog interception
        if self.load_modal.is_open:
            if self.load_modal.handle_event(event):
                return
        if self.osm_modal.is_open:
            if self.osm_modal.handle_event(event):
                return

        # Keyboard shortcuts (Undo, Redo, Delete)
        if event.type == pygame.KEYDOWN:
            mods = getattr(event, "mod", 0) | pygame.key.get_mods()
            is_ctrl = bool(mods & pygame.KMOD_CTRL)
            is_shift = bool(mods & pygame.KMOD_SHIFT)

            if is_ctrl and event.key == pygame.K_z:
                if is_shift:
                    self.redo()
                else:
                    self.undo()
                return
            elif is_ctrl and event.key == pygame.K_y:
                self.redo()
                return
            elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                self.delete_selected_node()
                return

        # 1. Mouse Scroll Wheel Zoom
        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if not self.view_rect.collidepoint(mx, my):
                mx, my = self.view_rect.centerx, self.view_rect.centery

            # Zoom in/out centered around cursor
            wx_before, wy_before = self.camera.screen_to_world(mx, my, self.view_rect)
            factor = 1.15 if event.y > 0 else 0.87
            new_zoom = max(0.2, min(5.0, self.camera.zoom * factor))
            self.camera.zoom = new_zoom
            self.camera.target_zoom = new_zoom

            # Adjust camera pos so cursor remains anchored over same world point
            wx_after, wy_after = self.camera.screen_to_world(mx, my, self.view_rect)
            self.camera.x += wx_before - wx_after
            self.camera.y += wy_before - wy_after
            self.camera.target_x = self.camera.x
            self.camera.target_y = self.camera.y
            self.status_message = f"Zoom: {int(self.camera.zoom * 100)}%"
            return

        # 2. Mouse Button Press
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Side Control Panel Click
            if self.panel_rect.collidepoint(mx, my):
                self._handle_panel_click(mx, my, event.button)
                return

            # Canvas interactions
            if self.view_rect.collidepoint(mx, my):
                wx, wy = self.camera.screen_to_world(mx, my, self.view_rect)

                if event.button == 1:  # Left click: Select or Drag node
                    clicked_idx = self._get_node_at(wx, wy)
                    mods = pygame.key.get_mods()
                    is_shift = bool(mods & pygame.KMOD_SHIFT)

                    if clicked_idx is not None:
                        if is_shift:
                            self.selected_node_b = clicked_idx
                            self.status_message = f"Selected End Node #{clicked_idx + 1}."
                        else:
                            self.selected_node_a = clicked_idx
                            self.is_dragging = True
                            self._drag_start_state = self._get_state_snapshot()
                            w = (
                                self.circuit.node_widths[clicked_idx]
                                if clicked_idx < len(self.circuit.node_widths)
                                else self.circuit.width
                            )
                            self.status_message = f"Selected Point #{clicked_idx + 1} (Width: {w:.1f}m)."
                    else:
                        self._insert_node_at(wx, wy)
                        self.is_dragging = True

                elif event.button in (2, 3):  # Right or Middle click: Delete node or Pan canvas
                    clicked_idx = self._get_node_at(wx, wy)
                    if clicked_idx is not None:
                        self.selected_node_a = clicked_idx
                        self.delete_selected_node()
                        return
                    else:
                        self.is_panning = True
                        self.pan_start = (mx, my)

        # 3. Mouse Button Release
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.is_dragging:
                    self.is_dragging = False
                    if self._drag_start_state:
                        if self._drag_start_state["control_points"] != self.circuit.control_points:
                            self._push_undo(self._drag_start_state)
                        self._drag_start_state = None
            elif event.button in (2, 3):
                self.is_panning = False

        # 4. Mouse Motion
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.view_rect.collidepoint(mx, my):
                wx, wy = self.camera.screen_to_world(mx, my, self.view_rect)
                self.hovered_node_idx = self._get_node_at(wx, wy)

                # Drag node
                if self.is_dragging and self.selected_node_a is not None:
                    if 0 <= self.selected_node_a < len(self.circuit.control_points):
                        self.circuit.control_points[self.selected_node_a] = (wx, wy)
                        self.circuit.build_circuit()

                # Pan canvas
                elif self.is_panning:
                    dx = mx - self.pan_start[0]
                    dy = my - self.pan_start[1]
                    self.camera.x -= dx / self.camera.zoom
                    self.camera.y -= dy / self.camera.zoom
                    self.camera.target_x = self.camera.x
                    self.camera.target_y = self.camera.y
                    self.pan_start = (mx, my)

    def _get_node_at(self, wx: float, wy: float, threshold_m: float = 24.0) -> Optional[int]:
        for i, (nx, ny) in enumerate(self.circuit.control_points):
            dist = math.hypot(wx - nx, wy - ny)
            if dist < threshold_m:
                return i
        return None

    def _insert_node_at(self, wx: float, wy: float):
        self._push_undo()
        pts = self.circuit.control_points
        if len(pts) < 3:
            pts.append((wx, wy))
            self.circuit.node_widths.append(14.0)
            self.circuit.set_control_points(pts, self.circuit.node_widths)
            self.selected_node_a = len(pts) - 1
            return

        best_idx = len(pts)
        min_dist = float("inf")
        for i in range(len(pts)):
            next_i = (i + 1) % len(pts)
            p1 = pts[i]
            p2 = pts[next_i]
            mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            d = math.hypot(wx - mx, wy - my)
            if d < min_dist:
                min_dist = d
                best_idx = i + 1

        pts.insert(best_idx, (wx, wy))
        prev_w = self.circuit.node_widths[best_idx - 1] if best_idx - 1 < len(self.circuit.node_widths) else 14.0
        self.circuit.node_widths.insert(best_idx, prev_w)
        self.circuit.set_control_points(pts, self.circuit.node_widths)
        self.selected_node_a = best_idx
        self.status_message = f"Point #{best_idx + 1} added (Width: {prev_w:.1f}m)."

    def add_drs_between_nodes(self, node_a: int, node_b: int):
        if (
            not self.circuit.node_s_distances
            or node_a >= len(self.circuit.node_s_distances)
            or node_b >= len(self.circuit.node_s_distances)
        ):
            return

        start_s = self.circuit.node_s_distances[node_a]
        end_s = self.circuit.node_s_distances[node_b]

        zone_name = f"DRS #{node_a + 1}->#{node_b + 1}"
        new_zone = {"name": zone_name, "node_a": node_a, "node_b": node_b, "start_s": start_s, "end_s": end_s}
        self.circuit.drs_zones.append(new_zone)
        self.status_message = f"Placed {zone_name}."

    def _handle_panel_click(self, mx: int, my: int, button: int):
        btns = self._get_panel_buttons()

        # 0. History & Node Deletion
        if btns["undo"].collidepoint(mx, my):
            self.undo()
            return
        elif btns["redo"].collidepoint(mx, my):
            self.redo()
            return
        elif btns["delete_node"].collidepoint(mx, my):
            self.delete_selected_node()
            return

        # 1. Fit Camera & Zoom Controls
        if btns["fit"].collidepoint(mx, my):
            self.camera.fit_circuit(self.circuit, self.view_rect)
            self.camera.x = self.camera.overview_x
            self.camera.y = self.camera.overview_y
            self.camera.zoom = self.camera.overview_zoom
            self.camera.target_x = self.camera.overview_x
            self.camera.target_y = self.camera.overview_y
            self.camera.target_zoom = self.camera.overview_zoom
            self.status_message = "Camera fitted to circuit overview."
            return

        elif btns["zoom_in"].collidepoint(mx, my):
            self.camera.zoom = min(5.0, self.camera.zoom * 1.25)
            self.camera.target_zoom = self.camera.zoom
            self.status_message = f"Zoom: {int(self.camera.zoom * 100)}%"
            return
        elif btns["zoom_out"].collidepoint(mx, my):
            self.camera.zoom = max(0.2, self.camera.zoom * 0.8)
            self.camera.target_zoom = self.camera.zoom
            self.status_message = f"Zoom: {int(self.camera.zoom * 100)}%"
            return

        # 2. Section Width (+ / -)
        if btns["width_plus"].collidepoint(mx, my):
            if self.selected_node_a is not None and self.selected_node_a < len(self.circuit.node_widths):
                self._push_undo()
                curr = self.circuit.node_widths[self.selected_node_a]
                self.circuit.set_node_width(self.selected_node_a, curr + 1.0)
                self.status_message = f"Node #{self.selected_node_a + 1} width increased to {curr + 1.0:.1f}m."
            return
        elif btns["width_minus"].collidepoint(mx, my):
            if self.selected_node_a is not None and self.selected_node_a < len(self.circuit.node_widths):
                self._push_undo()
                curr = self.circuit.node_widths[self.selected_node_a]
                self.circuit.set_node_width(self.selected_node_a, curr - 1.0)
                self.status_message = f"Node #{self.selected_node_a + 1} width decreased to {curr - 1.0:.1f}m."
            return

        # 3. Apply Width to Span or All
        if btns["span_width"].collidepoint(mx, my):
            if self.selected_node_a is not None and self.selected_node_b is not None:
                self._push_undo()
                src_w = self.circuit.node_widths[self.selected_node_a]
                a, b = min(self.selected_node_a, self.selected_node_b), max(self.selected_node_a, self.selected_node_b)
                for idx in range(a, b + 1):
                    if idx < len(self.circuit.node_widths):
                        self.circuit.node_widths[idx] = src_w
                self.circuit.build_circuit()
                self.status_message = f"Applied width {src_w:.1f}m to Nodes #{a + 1}..#{b + 1}."
            return
        elif btns["all_width"].collidepoint(mx, my):
            if self.selected_node_a is not None:
                self._push_undo()
                src_w = self.circuit.node_widths[self.selected_node_a]
                self.circuit.node_widths = [src_w] * len(self.circuit.control_points)
                self.circuit.build_circuit()
                self.status_message = f"Set entire circuit width to {src_w:.1f}m."
            return

        # 4. Add DRS Zone on Selected Nodes A -> B
        if btns["add_drs"].collidepoint(mx, my):
            if self.selected_node_a is not None and self.selected_node_b is not None:
                if self.selected_node_a != self.selected_node_b:
                    self._push_undo()
                    self.add_drs_between_nodes(self.selected_node_a, self.selected_node_b)
                else:
                    self.status_message = "Select two different nodes (Start & End) for DRS."
            return

        # 5. Check Individual DRS Zone Deletion buttons (fixed row positions: py + 204 + idx * 20)
        drs_y_start = self.panel_rect.y + 204
        for idx in range(min(2, len(self.circuit.drs_zones))):
            del_rect = pygame.Rect(self.panel_rect.x + self.panel_rect.width - 36, drs_y_start + idx * 20, 26, 18)
            if del_rect.collidepoint(mx, my):
                self._push_undo()
                del self.circuit.drs_zones[idx]
                self.status_message = "DRS zone removed."
                return

        # 6. Clear All DRS
        if btns["clear_drs"].collidepoint(mx, my):
            if self.circuit.drs_zones:
                self._push_undo()
                self.circuit.drs_zones = []
                self.status_message = "All DRS zones cleared."
            return

        # 7. PIT LANE CONTROLS
        if btns["set_pit_in"].collidepoint(mx, my):
            if self.selected_node_a is not None:
                self._push_undo()
                self.circuit.pit_entry_node = self.selected_node_a
                self.circuit.build_circuit()
                self.status_message = f"Pit Entry set to Node #{self.selected_node_a + 1}."
            return
        elif btns["set_pit_out"].collidepoint(mx, my):
            node_out = self.selected_node_b if self.selected_node_b is not None else self.selected_node_a
            if node_out is not None:
                self._push_undo()
                self.circuit.pit_exit_node = node_out
                self.circuit.build_circuit()
                self.status_message = f"Pit Exit set to Node #{node_out + 1}."
            return
        elif btns["toggle_pit_side"].collidepoint(mx, my):
            self._push_undo()
            self.circuit.pit_side = "OUTSIDE" if self.circuit.pit_side == "INSIDE" else "INSIDE"
            self.circuit.build_circuit()
            self.status_message = f"Pit Lane placed on {self.circuit.pit_side}."
            return
        elif btns["cycle_pit_offset"].collidepoint(mx, my):
            self._push_undo()
            offsets = [10.0, 14.0, 18.0, 22.0]
            next_idx = (
                (offsets.index(self.circuit.pit_offset_m) + 1) % len(offsets)
                if self.circuit.pit_offset_m in offsets
                else 1
            )
            self.circuit.pit_offset_m = offsets[next_idx]
            self.circuit.build_circuit()
            self.status_message = f"Pit Lane spacing set to {self.circuit.pit_offset_m:.0f}m."
            return

        # 8. Free 5-Compound Selection Chips (C1 to C5)
        chips = self._get_compound_chip_rects()
        for c_key, tier, r in chips:
            if r.collidepoint(mx, my):
                self._push_undo()
                if c_key in self.circuit.nominated_compounds:
                    if len(self.circuit.nominated_compounds) > 1:
                        self.circuit.nominated_compounds.remove(c_key)
                else:
                    if len(self.circuit.nominated_compounds) >= 3:
                        self.circuit.nominated_compounds.pop(0)
                    self.circuit.nominated_compounds.append(c_key)

                self.circuit.nominated_compounds = [
                    c for c in DRY_COMPOUND_KEYS if c in self.circuit.nominated_compounds
                ]
                selected_tiers = [TIRE_COMPOUNDS[c].tier for c in self.circuit.nominated_compounds]
                self.status_message = f"Selected Tyre Trio: {', '.join(selected_tiers)}"
                return

        # 9. Save Track to JSON
        if btns["save_json"].collidepoint(mx, my):
            os.makedirs("tracks", exist_ok=True)
            safe_name = self.circuit.name.lower().replace(" ", "_") + ".json"
            save_path = os.path.join("tracks", safe_name)
            self.circuit.save_json(save_path)
            self.status_message = f"Saved circuit to {save_path}!"
            return

        # 10. Load Track from JSON
        if btns["load_json"].collidepoint(mx, my):
            self.load_modal.open()
            self.status_message = "Opened Track Loader. Select a circuit to load!"
            return

        # 11. Reset Track
        if btns["reset_track"].collidepoint(mx, my):
            self._push_undo()
            pts = [(-200, -100), (0, -100), (200, -100), (200, 100), (0, 100), (-200, 100)]
            self.circuit.set_control_points(pts, [14.0] * len(pts))
            self.circuit.drs_zones = []
            self.circuit.nominated_compounds = ["HARD", "SOFT", "SUPERSOFT"]
            self.circuit.set_pit_lane_endpoints(entry_node=5, exit_node=1, side="INSIDE", offset_m=14.0)
            self.selected_node_a = 0
            self.selected_node_b = 2
            self.status_message = "Circuit reset to basic template."
            return

        # 11. Open Real-World Road Map Importer (OSM)
        if btns["import_osm"].collidepoint(mx, my):
            self.osm_modal.open()
            self.status_message = "Opened OpenStreetMap Importer. Search any city to fetch public roads!"
            return

        # 12. Add to Career Championship Season Calendar
        if btns["add_to_calendar"].collidepoint(mx, my):
            os.makedirs("tracks", exist_ok=True)
            safe_name = self.circuit.name.lower().replace(" ", "_") + ".json"
            save_path = os.path.join("tracks", safe_name)
            self.circuit.save_json(save_path)
            try:
                from ..database.career_db import CareerDatabase

                cdb = CareerDatabase("career.db")
                rnd = cdb.add_calendar_round(self.circuit.name, safe_name, total_laps=16, weather_profile="DYNAMIC")
                self.status_message = f"Track '{self.circuit.name}' added to Season Calendar as Round {rnd}!"
            except Exception as ex:
                self.status_message = f"Could not add to calendar: {ex}"
            return

        # 12. TEST RACE ON THIS TRACK!
        if btns["race_now"].collidepoint(mx, my):
            if len(self.circuit.control_points) >= 3 and self.circuit.length > 50:
                self.on_test_race(self.circuit)
            else:
                self.status_message = "Need at least 3 control points to race."
            return

    def render(self, surface: pygame.Surface):
        # 1. Render Track & Canvas (Including Pit Lane)
        self.track_renderer.render(surface, self.circuit, self.camera, self.view_rect)

        # 2. Draw Editor Control Nodes (always show indices so no control points are hidden)
        turn_map = self.circuit.get_turn_node_indices()
        drs_start_nodes = {z.get("node_a") for z in self.circuit.drs_zones if z.get("node_a") is not None}
        drs_end_nodes = {z.get("node_b") for z in self.circuit.drs_zones if z.get("node_b") is not None}

        for i, (nx, ny) in enumerate(self.circuit.control_points):
            sx, sy = self.camera.world_to_screen(nx, ny, self.view_rect)
            is_a = i == self.selected_node_a
            is_b = i == self.selected_node_b
            is_pit_in = i == self.circuit.pit_entry_node
            is_pit_out = i == self.circuit.pit_exit_node
            is_drs_start = i in drs_start_nodes
            is_drs_end = i in drs_end_nodes
            is_hov = i == self.hovered_node_idx
            turn_num = turn_map.get(i)
            is_turn = turn_num is not None

            # Highlight special nodes clearly; all regular control points remain clearly visible and interactive
            if is_a or is_b or is_hov or is_pit_in or is_pit_out or is_drs_start or is_drs_end:
                rad = 8
            elif is_turn:
                rad = 7
            else:
                rad = 5  # Clearly visible, clickable control node

            if is_a:
                col = (255, 215, 0)
                pygame.draw.circle(surface, (255, 240, 120), (sx, sy), rad + 3, 2)
            elif is_b:
                col = (0, 240, 255)
                pygame.draw.circle(surface, (120, 255, 255), (sx, sy), rad + 3, 2)
            elif is_drs_start or is_drs_end:
                col = (0, 255, 120)
                pygame.draw.circle(surface, (180, 255, 200), (sx, sy), rad + 2, 2)
            elif is_pit_in:
                col = (240, 210, 40)
                pygame.draw.circle(surface, (255, 235, 120), (sx, sy), rad + 2, 2)
            elif is_pit_out:
                col = (40, 230, 100)
                pygame.draw.circle(surface, (140, 255, 170), (sx, sy), rad + 2, 2)
            elif is_hov:
                col = (255, 180, 50)
                pygame.draw.circle(surface, (255, 220, 140), (sx, sy), rad + 2, 1)
            elif is_turn:
                col = (255, 90, 90)  # Bright red/coral checkpoint marker for real corner
                pygame.draw.circle(surface, (255, 200, 200), (sx, sy), rad + 1, 1)
            else:
                col = (130, 175, 210)  # Visible slate blue for straight/intermediate control points

            pygame.draw.circle(surface, col, (sx, sy), rad)
            pygame.draw.circle(surface, (10, 12, 16), (sx, sy), rad, 1)

            node_w = self.circuit.node_widths[i] if i < len(self.circuit.node_widths) else 14.0

            # Badge text: ALWAYS show node index #{i+1} alongside any roles so no points are ever missing!
            roles = []
            if is_turn:
                roles.append(f"T{turn_num}")
            if is_a:
                roles.append("A")
            if is_b:
                roles.append("B")
            if is_drs_start:
                roles.append("DRS IN")
            if is_drs_end:
                roles.append("DRS OUT")
            if is_pit_in:
                roles.append("PIT IN")
            if is_pit_out:
                roles.append("PIT OUT")

            tag = f"#{i + 1}"
            if roles:
                tag += " [" + "/".join(roles) + "]"
            tag += f" ({node_w:.0f}m)"

            if is_a:
                text_col = (255, 235, 100)
            elif is_b:
                text_col = (100, 240, 255)
            elif is_drs_start or is_drs_end:
                text_col = (100, 255, 160)
            elif is_pit_in or is_pit_out:
                text_col = (255, 230, 100)
            elif is_turn:
                text_col = (255, 200, 200)
            elif is_hov:
                text_col = (255, 210, 140)
            else:
                text_col = (190, 210, 230)

            lbl = self.font_badge.render(tag, True, text_col)
            bg_rect = pygame.Rect(sx + 7, sy - 8, lbl.get_width() + 4, lbl.get_height() + 1)
            pygame.draw.rect(surface, (12, 16, 22), bg_rect, border_radius=3)
            surface.blit(lbl, (sx + 9, sy - 8))

        # 3. Render Side Control Panel
        UITheme.draw_panel(surface, self.panel_rect)

        # Header
        hdr_rect = pygame.Rect(self.panel_rect.x, self.panel_rect.y, self.panel_rect.width, 26)
        pygame.draw.rect(surface, UITheme.PANEL_HEADER, hdr_rect, border_top_left_radius=4, border_top_right_radius=4)
        h_txt = self.font_title.render("CIRCUIT DESIGNER", True, UITheme.ACCENT_CYAN)
        surface.blit(h_txt, (self.panel_rect.x + 10, self.panel_rect.y + 5))

        # Track Stats
        km_len = self.circuit.length / 1000.0
        n_corners = self.circuit.corners_count
        stats1 = f"Length: {km_len:04.2f} km | Turns: {n_corners} | Nodes: {len(self.circuit.control_points)}"

        cur_w = (
            self.circuit.node_widths[self.selected_node_a]
            if self.selected_node_a is not None and self.selected_node_a < len(self.circuit.node_widths)
            else 14.0
        )
        node_a_str = f"#{self.selected_node_a + 1}" if self.selected_node_a is not None else "None"
        node_b_str = f"#{self.selected_node_b + 1}" if self.selected_node_b is not None else "None"
        stats2 = f"Node {node_a_str} Width: {cur_w:.1f}m | Span: {node_a_str}->{node_b_str}"

        surface.blit(
            self.font_desc.render(stats1, True, UITheme.TEXT_WHITE), (self.panel_rect.x + 10, self.panel_rect.y + 30)
        )
        surface.blit(
            self.font_desc.render(stats2, True, UITheme.ACCENT_YELLOW), (self.panel_rect.x + 10, self.panel_rect.y + 46)
        )

        # Render Row 1: Undo / Redo / Delete Node Buttons (y = py + 70)
        btns = self._get_panel_buttons()
        UITheme.draw_button(surface, btns["undo"], "UNDO", self.font_btn)
        UITheme.draw_button(surface, btns["redo"], "REDO", self.font_btn)

        # Danger button styling for Delete Node
        del_node_bg = (160, 36, 36)
        del_node_border = (220, 60, 60)
        pygame.draw.rect(surface, del_node_bg, btns["delete_node"], border_radius=3)
        pygame.draw.rect(surface, del_node_border, btns["delete_node"], width=1, border_radius=3)
        del_node_txt = self.font_btn.render("DEL POINT", True, (255, 255, 255))
        surface.blit(
            del_node_txt,
            (
                btns["delete_node"].x + (btns["delete_node"].width - del_node_txt.get_width()) // 2,
                btns["delete_node"].y + 3,
            ),
        )

        # Render Row 2: View & Zoom Buttons (y = py + 96)
        UITheme.draw_button(surface, btns["fit"], "FIT VIEW", self.font_btn)
        UITheme.draw_button(surface, btns["zoom_in"], "ZOOM +", self.font_btn)
        UITheme.draw_button(surface, btns["zoom_out"], "ZOOM -", self.font_btn)

        # Width buttons (y = py + 122 & py + 150)
        UITheme.draw_button(surface, btns["width_plus"], f"WIDTH + ({cur_w + 1:.0f}m)", self.font_btn)
        UITheme.draw_button(surface, btns["width_minus"], f"WIDTH - ({cur_w - 1:.0f}m)", self.font_btn)
        UITheme.draw_button(surface, btns["span_width"], "SPAN WIDTH", self.font_btn)
        UITheme.draw_button(surface, btns["all_width"], "ALL WIDTH", self.font_btn)

        # DRS Button (y = py + 176)
        pygame.draw.rect(surface, (0, 180, 90), btns["add_drs"], border_radius=3)
        pygame.draw.rect(surface, (0, 240, 120), btns["add_drs"], width=1, border_radius=3)
        d_txt = self.font_btn.render(f"+ SET DRS: {node_a_str} -> {node_b_str}", True, (255, 255, 255))
        surface.blit(
            d_txt, (btns["add_drs"].x + (btns["add_drs"].width - d_txt.get_width()) // 2, btns["add_drs"].y + 4)
        )

        # DRS List (y = py + 204)
        drs_y_start = self.panel_rect.y + 204
        for idx in range(min(2, len(self.circuit.drs_zones))):
            zone = self.circuit.drs_zones[idx]
            z_rect = pygame.Rect(self.panel_rect.x + 10, drs_y_start + idx * 20, self.panel_rect.width - 50, 16)
            pygame.draw.rect(surface, (28, 36, 44), z_rect, border_radius=2)
            z_txt = self.font_desc.render(zone.get("name", f"DRS {idx + 1}"), True, UITheme.ACCENT_GREEN)
            surface.blit(z_txt, (z_rect.x + 6, z_rect.y + 1))

            del_rect = pygame.Rect(self.panel_rect.x + self.panel_rect.width - 36, drs_y_start + idx * 20, 26, 16)
            pygame.draw.rect(surface, (180, 40, 40), del_rect, border_radius=2)
            del_txt = self.font_badge.render("X", True, (255, 255, 255))
            surface.blit(del_txt, (del_rect.x + 8, del_rect.y + 1))

        # Clear DRS Button (y = py + 248)
        UITheme.draw_button(surface, btns["clear_drs"], "CLEAR ALL DRS", self.font_btn)

        # PIT LANE DESIGNER SECTION (y = py + 272)
        pit_hdr = self.font_desc.render(
            f"PIT LANE: #{self.circuit.pit_entry_node + 1} -> #{self.circuit.pit_exit_node + 1} [{self.circuit.pit_side}]",
            True,
            (240, 210, 40),
        )
        surface.blit(pit_hdr, (self.panel_rect.x + 10, self.panel_rect.y + 272))

        UITheme.draw_button(surface, btns["set_pit_in"], f"PIT IN: #{node_a_str}", self.font_btn)
        UITheme.draw_button(surface, btns["set_pit_out"], f"PIT OUT: #{node_b_str}", self.font_btn)
        UITheme.draw_button(surface, btns["toggle_pit_side"], f"SIDE: {self.circuit.pit_side[:3]}", self.font_btn)
        UITheme.draw_button(
            surface, btns["cycle_pit_offset"], f"OFFSET: {self.circuit.pit_offset_m:.0f}m", self.font_btn
        )

        # Free 5-Compound Selection Chips (C1 to C5) at y = py + 344
        t_hdr = self.font_desc.render("TYRES (PICK 3):", True, UITheme.TEXT_MUTED)
        surface.blit(t_hdr, (self.panel_rect.x + 10, self.panel_rect.y + 344))

        chips = self._get_compound_chip_rects()
        for c_key, tier, r in chips:
            comp = TIRE_COMPOUNDS[c_key]
            is_selected = c_key in self.circuit.nominated_compounds
            bg_col = (45, 55, 75) if is_selected else (22, 26, 34)
            border_col = comp.color_rgb if is_selected else (60, 68, 80)

            pygame.draw.rect(surface, bg_col, r, border_radius=3)
            pygame.draw.rect(surface, border_col, r, width=2 if is_selected else 1, border_radius=3)

            pygame.draw.circle(surface, comp.color_rgb, (r.x + 10, r.y + 12), 4)
            t_lbl = self.font_badge.render(tier, True, (255, 255, 255) if is_selected else UITheme.TEXT_MUTED)
            surface.blit(t_lbl, (r.x + 18, r.y + 5))

        # Save Track & Load Track (y = py + 388)
        UITheme.draw_button(surface, btns["save_json"], "SAVE TRACK", self.font_btn)
        UITheme.draw_button(surface, btns["load_json"], "LOAD TRACK", self.font_btn)

        # Import Road Map & Reset Track (y = py + 416)
        pygame.draw.rect(surface, (28, 45, 60), btns["import_osm"], border_radius=3)
        pygame.draw.rect(surface, (0, 180, 240), btns["import_osm"], width=1, border_radius=3)
        osm_txt = self.font_btn.render("IMPORT OSM", True, (0, 220, 255))
        surface.blit(
            osm_txt,
            (btns["import_osm"].x + (btns["import_osm"].width - osm_txt.get_width()) // 2, btns["import_osm"].y + 3),
        )

        UITheme.draw_button(surface, btns["reset_track"], "RESET TRACK", self.font_btn)

        # Add to Season Calendar Button (y = py + 444)
        pygame.draw.rect(surface, (30, 48, 70), btns["add_to_calendar"], border_radius=3)
        pygame.draw.rect(surface, (0, 220, 255), btns["add_to_calendar"], width=1, border_radius=3)
        cal_txt = self.font_badge.render("+ ADD TO CAREER CALENDAR", True, (0, 240, 255))
        surface.blit(
            cal_txt,
            (
                btns["add_to_calendar"].x + (btns["add_to_calendar"].width - cal_txt.get_width()) // 2,
                btns["add_to_calendar"].y + 4,
            ),
        )

        # Race Button (y = py + 472)
        pygame.draw.rect(surface, (0, 200, 120), btns["race_now"], border_radius=4)
        t_txt = self.font_btn.render("RACE ON THIS TRACK >>", True, (10, 20, 20))
        surface.blit(
            t_txt, (btns["race_now"].x + (btns["race_now"].width - t_txt.get_width()) // 2, btns["race_now"].y + 8)
        )

        # Bottom Status Message Bar
        stat_bar = pygame.Rect(self.view_rect.x, self.view_rect.bottom - 24, self.view_rect.width, 24)
        pygame.draw.rect(surface, (16, 20, 26), stat_bar, border_radius=3)
        msg_surf = self.font_desc.render(self.status_message, True, UITheme.TEXT_WHITE)
        surface.blit(msg_surf, (stat_bar.x + 10, stat_bar.y + 4))

        # 4. Render Modals
        if self.osm_modal.is_open:
            self.osm_modal.render(surface)
        if self.load_modal.is_open:
            self.load_modal.render(surface)
