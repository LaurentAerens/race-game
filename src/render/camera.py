from typing import Optional, Tuple

import pygame

from ..core.car import Car
from ..core.circuit import Circuit


class Camera:
    """Smooth 2D Camera supporting Track Overview and Follow Car tracking."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.x: float = 0.0
        self.y: float = 0.0
        self.zoom: float = 1.0

        # Target position & zoom for smooth interpolation
        self.target_x: float = 0.0
        self.target_y: float = 0.0
        self.target_zoom: float = 1.0

        # Stored overview values for fitting circuit
        self.overview_x: float = 0.0
        self.overview_y: float = 0.0
        self.overview_zoom: float = 1.0

        self.mode: str = "TRACK_OVERVIEW"  # "TRACK_OVERVIEW" or "FOLLOW_CAR"
        self.followed_car: Optional[Car] = None

    def fit_circuit(self, circuit: Circuit, view_rect: pygame.Rect):
        """Calculates optimal zoom and center offset to fit the whole circuit in view_rect."""
        if len(circuit.points) == 0:
            return

        min_x = float(circuit.points[:, 0].min()) - 40.0
        max_x = float(circuit.points[:, 0].max()) + 40.0
        min_y = float(circuit.points[:, 1].min()) - 40.0
        max_y = float(circuit.points[:, 1].max()) + 40.0

        track_w = max(50.0, max_x - min_x)
        track_h = max(50.0, max_y - min_y)

        self.overview_x = (min_x + max_x) / 2.0
        self.overview_y = (min_y + max_y) / 2.0

        zoom_x = view_rect.width / track_w
        zoom_y = view_rect.height / track_h
        self.overview_zoom = min(zoom_x, zoom_y) * 0.92

        if self.mode == "TRACK_OVERVIEW":
            self.target_x = self.overview_x
            self.target_y = self.overview_y
            self.target_zoom = self.overview_zoom
            # If camera was at default (0, 0), snap immediately
            if self.x == 0.0 and self.y == 0.0:
                self.x = self.overview_x
                self.y = self.overview_y
                self.zoom = self.overview_zoom

    def set_overview_mode(self, circuit: Optional[Circuit] = None, view_rect: Optional[pygame.Rect] = None):
        """Switches to overview mode and transitions camera back to whole-track view."""
        self.mode = "TRACK_OVERVIEW"
        self.followed_car = None
        if circuit and view_rect:
            self.fit_circuit(circuit, view_rect)
        else:
            self.target_x = self.overview_x
            self.target_y = self.overview_y
            self.target_zoom = self.overview_zoom

    def set_follow_car(self, car: Car):
        """Focuses camera to follow a specific car."""
        self.mode = "FOLLOW_CAR"
        self.followed_car = car
        self.target_zoom = 1.85

    def update(self, dt: float, view_rect: pygame.Rect):
        """Smoothly interpolates camera position and zoom towards targets."""
        if self.mode == "FOLLOW_CAR" and self.followed_car:
            self.target_x = self.followed_car.world_x
            self.target_y = self.followed_car.world_y
            self.target_zoom = 1.85
        elif self.mode == "TRACK_OVERVIEW":
            self.target_x = self.overview_x
            self.target_y = self.overview_y
            self.target_zoom = self.overview_zoom

        # Smooth camera movement
        lerp_speed = min(1.0, 7.0 * dt)
        zoom_lerp = min(1.0, 5.0 * dt)

        self.x += (self.target_x - self.x) * lerp_speed
        self.y += (self.target_y - self.y) * lerp_speed
        self.zoom += (self.target_zoom - self.zoom) * zoom_lerp

    def world_to_screen(self, wx: float, wy: float, view_rect: pygame.Rect) -> Tuple[int, int]:
        """Converts world coordinates to screen pixel coordinates."""
        cx = view_rect.x + view_rect.width / 2.0
        cy = view_rect.y + view_rect.height / 2.0

        sx = cx + (wx - self.x) * self.zoom
        sy = cy + (wy - self.y) * self.zoom
        return (int(sx), int(sy))

    def screen_to_world(self, sx: int, sy: int, view_rect: pygame.Rect) -> Tuple[float, float]:
        """Converts screen pixel coordinates to world coordinates."""
        cx = view_rect.x + view_rect.width / 2.0
        cy = view_rect.y + view_rect.height / 2.0

        wx = self.x + (sx - cx) / max(0.001, self.zoom)
        wy = self.y + (sy - cy) / max(0.001, self.zoom)
        return (wx, wy)
