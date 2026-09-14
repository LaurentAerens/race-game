import json
import math
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame

from src.core.circuit import Circuit
from src.ui.theme import UITheme


class LoadTrackModal:
    """
    Modal dialog allowing users to select and load any saved track from the
    /tracks directory, or browse their disk for any circuit JSON file.
    """

    def __init__(self, on_track_loaded: Callable[[Circuit], None]):
        self.on_track_loaded = on_track_loaded
        self.is_open: bool = False
        self.track_items: List[Dict[str, Any]] = []
        self.selected_idx: int = 0
        self.scroll_offset: int = 0
        self.status_message: str = ""
        self.search_query: str = ""
        self.search_active: bool = False

        # Fonts
        self.font_title: Optional[pygame.font.Font] = None
        self.font_bold: Optional[pygame.font.Font] = None
        self.font_ui: Optional[pygame.font.Font] = None
        self.font_small: Optional[pygame.font.Font] = None

        # Layout rects
        self.modal_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_rects: Dict[str, pygame.Rect] = {}
        self.item_rects: List[Tuple[pygame.Rect, pygame.Rect, int]] = []  # (item_box, load_btn, track_idx)

    def _init_fonts(self):
        if self.font_title is None:
            self.font_title = UITheme.get_font(16, bold=True)
            self.font_bold = UITheme.get_font(13, bold=True)
            self.font_ui = UITheme.get_font(13, bold=False)
            self.font_small = UITheme.get_font(11, bold=False)

    def open(self):
        self.is_open = True
        self.selected_idx = 0
        self.scroll_offset = 0
        self.search_query = ""
        self.search_active = False
        self.status_message = "Select a track to load, or click 'BROWSE FILE...' to pick a JSON from disk."
        self.refresh_tracks()

    def close(self):
        self.is_open = False

    def refresh_tracks(self):
        """Scans tracks/ folder and loads track metadata for all JSON files."""
        self.track_items.clear()
        tracks_dir = os.path.abspath("tracks")
        if not os.path.exists(tracks_dir):
            os.makedirs(tracks_dir, exist_ok=True)

        files = [f for f in os.listdir(tracks_dir) if f.lower().endswith(".json")]
        files.sort()

        for filename in files:
            filepath = os.path.join(tracks_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                pts = data.get("control_points", [])
                name = data.get("name", filename[:-5].replace("_", " ").title())
                avg_w = data.get("width", 12.0)
                n_pts = len(pts)

                # Estimate track length
                length_m = 0.0
                if n_pts >= 3:
                    for i in range(n_pts):
                        p1 = pts[i]
                        p2 = pts[(i + 1) % n_pts]
                        length_m += math.hypot(p2[0] - p1[0], p2[1] - p1[1])

                drs_count = len(data.get("drs_zones", []))
                mtime = os.path.getmtime(filepath)

                self.track_items.append(
                    {
                        "filepath": filepath,
                        "filename": filename,
                        "name": name,
                        "length_m": length_m,
                        "nodes": n_pts,
                        "width": avg_w,
                        "drs_count": drs_count,
                        "mtime": mtime,
                    }
                )
            except Exception as e:
                print(f"[LoadTrackModal] Error reading {filename}: {e}")

        # Sort by modification time (most recent first)
        self.track_items.sort(key=lambda x: x["mtime"], reverse=True)
        self.status_message = f"Found {len(self.track_items)} saved track(s) in /tracks directory."

    def _get_filtered_items(self) -> List[Tuple[int, Dict[str, Any]]]:
        if not self.search_query.strip():
            return list(enumerate(self.track_items))
        q = self.search_query.strip().lower()
        res = []
        for idx, item in enumerate(self.track_items):
            if q in item["name"].lower() or q in item["filename"].lower():
                res.append((idx, item))
        return res

    def _load_track_file(self, filepath: str):
        """Loads a track from filepath and triggers callback."""
        try:
            circuit = Circuit.load_json(filepath)
            if circuit and len(circuit.control_points) >= 3:
                self.on_track_loaded(circuit)
                self.close()
            else:
                self.status_message = "Invalid track: Circuit must have at least 3 control points."
        except Exception as e:
            self.status_message = f"Failed to load track: {e}"

    def _browse_file_dialog(self):
        """Opens native OS file chooser to select any JSON file on disk."""
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            initial_dir = os.path.abspath("tracks") if os.path.exists("tracks") else os.getcwd()
            picked_path = filedialog.askopenfilename(
                title="Select Circuit JSON File",
                filetypes=[("Circuit JSON (*.json)", "*.json"), ("All Files (*.*)", "*.*")],
                initialdir=initial_dir,
            )
            root.destroy()
            if picked_path and os.path.exists(picked_path):
                self._load_track_file(picked_path)
        except Exception as e:
            self.status_message = f"File dialog error: {e}"

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            elif self.search_active:
                if event.key == pygame.K_BACKSPACE:
                    self.search_query = self.search_query[:-1]
                elif event.key == pygame.K_RETURN:
                    self.search_active = False
                elif event.unicode and event.unicode.isprintable():
                    self.search_query += event.unicode
                return True
            elif event.key == pygame.K_UP:
                filtered = self._get_filtered_items()
                if filtered:
                    self.selected_idx = max(0, self.selected_idx - 1)
                return True
            elif event.key == pygame.K_DOWN:
                filtered = self._get_filtered_items()
                if filtered:
                    self.selected_idx = min(len(filtered) - 1, self.selected_idx + 1)
                return True
            elif event.key == pygame.K_RETURN:
                filtered = self._get_filtered_items()
                if filtered and 0 <= self.selected_idx < len(filtered):
                    orig_idx, item = filtered[self.selected_idx]
                    self._load_track_file(item["filepath"])
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Handle search bar click
            if self.btn_rects.get("search_bar") and self.btn_rects["search_bar"].collidepoint(mx, my):
                self.search_active = True
                return True
            else:
                self.search_active = False

            # Check buttons
            if self.btn_rects.get("close") and self.btn_rects["close"].collidepoint(mx, my):
                self.close()
                return True
            elif self.btn_rects.get("browse") and self.btn_rects["browse"].collidepoint(mx, my):
                self._browse_file_dialog()
                return True
            elif self.btn_rects.get("cancel") and self.btn_rects["cancel"].collidepoint(mx, my):
                self.close()
                return True

            # Check track item row clicks
            for item_rect, btn_load_rect, orig_idx in self.item_rects:
                if btn_load_rect.collidepoint(mx, my):
                    self._load_track_file(self.track_items[orig_idx]["filepath"])
                    return True
                elif item_rect.collidepoint(mx, my):
                    self.selected_idx = orig_idx
                    if event.button == 1 and getattr(event, "clicks", 1) == 2:  # Double click
                        self._load_track_file(self.track_items[orig_idx]["filepath"])
                    return True

            # Mouse wheel scroll
            if event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 1)
                return True
            elif event.button == 5:  # Scroll down
                filtered = self._get_filtered_items()
                max_scroll = max(0, len(filtered) - 5)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
                return True

        return True  # Consume input while modal is open

    def render(self, screen: pygame.Surface):
        if not self.is_open:
            return

        self._init_fonts()
        sw, sh = screen.get_size()

        # Dim background
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 185))
        screen.blit(dim, (0, 0))

        # Main modal window: 620 x 480
        mw = 620
        mh = min(500, sh - 60)
        mx = (sw - mw) // 2
        my = (sh - mh) // 2
        self.modal_rect = pygame.Rect(mx, my, mw, mh)

        # Draw frame
        pygame.draw.rect(screen, (22, 26, 34), self.modal_rect, border_radius=8)
        pygame.draw.rect(screen, (55, 68, 85), self.modal_rect, width=2, border_radius=8)

        # Header bar
        hdr_rect = pygame.Rect(mx, my, mw, 44)
        pygame.draw.rect(screen, (30, 36, 48), hdr_rect, border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.line(screen, (45, 55, 70), (mx, my + 44), (mx + mw, my + 44), 1)

        title_surf = self.font_title.render("LOAD SAVED CIRCUIT (JSON)", True, (0, 220, 240))
        screen.blit(title_surf, (mx + 16, my + 11))

        # Close X button
        close_btn_rect = pygame.Rect(mx + mw - 36, my + 8, 28, 28)
        self.btn_rects["close"] = close_btn_rect
        pygame.draw.rect(screen, (180, 45, 45), close_btn_rect, border_radius=4)
        x_surf = self.font_bold.render("X", True, (255, 255, 255))
        screen.blit(x_surf, x_surf.get_rect(center=close_btn_rect.center))

        # Search / Filter Bar
        search_y = my + 54
        search_rect = pygame.Rect(mx + 16, search_y, mw - 32, 30)
        self.btn_rects["search_bar"] = search_rect
        border_col = (0, 200, 240) if self.search_active else (60, 70, 85)
        pygame.draw.rect(screen, (15, 18, 24), search_rect, border_radius=4)
        pygame.draw.rect(screen, border_col, search_rect, width=1, border_radius=4)

        disp_query = (
            self.search_query if self.search_query else ("Filter circuits by name..." if not self.search_active else "")
        )
        q_col = (255, 255, 255) if self.search_query else (120, 130, 145)
        q_surf = self.font_ui.render(disp_query, True, q_col)
        screen.blit(q_surf, (search_rect.x + 8, search_rect.y + 5))

        # Track list viewport
        list_y = search_y + 38
        list_h = mh - 146
        list_rect = pygame.Rect(mx + 16, list_y, mw - 32, list_h)
        pygame.draw.rect(screen, (17, 20, 27), list_rect, border_radius=4)
        pygame.draw.rect(screen, (40, 48, 60), list_rect, width=1, border_radius=4)

        # Render list items
        filtered = self._get_filtered_items()
        self.item_rects.clear()

        row_h = 58
        visible_rows = list_h // (row_h + 6)
        max_scroll = max(0, len(filtered) - visible_rows)
        self.scroll_offset = min(self.scroll_offset, max_scroll)

        clip_prev = screen.get_clip()
        screen.set_clip(list_rect)

        if not filtered:
            empty_txt = self.font_ui.render("No matching circuit JSON files found.", True, (130, 140, 155))
            screen.blit(empty_txt, empty_txt.get_rect(center=list_rect.center))
        else:
            for display_idx in range(visible_rows + 1):
                item_idx = self.scroll_offset + display_idx
                if item_idx >= len(filtered):
                    break

                orig_idx, item = filtered[item_idx]
                item_y = list_y + 6 + display_idx * (row_h + 6)
                item_rect = pygame.Rect(list_rect.x + 6, item_y, list_rect.width - 12, row_h)

                is_sel = item_idx == self.selected_idx
                bg_col = (36, 48, 68) if is_sel else (25, 30, 40)
                border_c = (0, 180, 240) if is_sel else (50, 60, 75)

                pygame.draw.rect(screen, bg_col, item_rect, border_radius=4)
                pygame.draw.rect(screen, border_c, item_rect, width=1, border_radius=4)

                # Track name (Bold)
                name_surf = self.font_bold.render(item["name"], True, (255, 255, 255))
                screen.blit(name_surf, (item_rect.x + 10, item_rect.y + 6))

                # Track Details line: length, nodes, width, DRS
                len_km = item["length_m"] / 1000.0
                detail_str = (
                    f"{item['filename']}  •  {len_km:.2f} km  •  {item['nodes']} nodes  •  {item['width']:.1f}m width"
                )
                if item["drs_count"] > 0:
                    detail_str += f"  •  {item['drs_count']} DRS"

                detail_surf = self.font_small.render(detail_str, True, (160, 175, 195))
                screen.blit(detail_surf, (item_rect.x + 10, item_rect.y + 32))

                # Load button on right
                btn_load = pygame.Rect(item_rect.right - 85, item_rect.y + 12, 75, 34)
                pygame.draw.rect(screen, (34, 139, 74), btn_load, border_radius=4)
                load_txt = self.font_bold.render("LOAD", True, (255, 255, 255))
                screen.blit(load_txt, load_txt.get_rect(center=btn_load.center))

                self.item_rects.append((item_rect, btn_load, orig_idx))

        screen.set_clip(clip_prev)

        # Bottom Action Bar
        bottom_y = my + mh - 44
        btn_browse = pygame.Rect(mx + 16, bottom_y, 140, 32)
        self.btn_rects["browse"] = btn_browse
        pygame.draw.rect(screen, (38, 70, 110), btn_browse, border_radius=4)
        browse_txt = self.font_bold.render("📁 BROWSE FILE...", True, (255, 255, 255))
        screen.blit(browse_txt, browse_txt.get_rect(center=btn_browse.center))

        btn_cancel = pygame.Rect(mx + 166, bottom_y, 90, 32)
        self.btn_rects["cancel"] = btn_cancel
        pygame.draw.rect(screen, (60, 65, 75), btn_cancel, border_radius=4)
        cancel_txt = self.font_ui.render("CANCEL", True, (220, 220, 220))
        screen.blit(cancel_txt, cancel_txt.get_rect(center=btn_cancel.center))

        # Status text on right
        status_surf = self.font_small.render(self.status_message, True, (180, 195, 215))
        screen.blit(status_surf, (mx + 270, bottom_y + 9))
