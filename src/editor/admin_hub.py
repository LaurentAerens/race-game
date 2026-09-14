from typing import Callable

import pygame

from ..core.circuit import Circuit
from ..ui.theme import UITheme
from .database_editor import DatabaseEditor
from .track_editor import TrackEditor


class AdminHub:
    """
    Unified Admin / Creator Tools Hub.
    Houses:
    - Track Editor (Circuit Designer CAD tool)
    - Database Editor (Car performance, Driver skills & Team liveries editor)
    - Back to Title Menu navigation
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        on_back_to_menu: Callable[[], None],
        on_test_race: Callable[[Circuit], None],
        exhibition_db_path: str = "race_game.db",
        career_db_path: str = "career.db",
    ):
        self.width = screen_width
        self.height = screen_height
        self.on_back_to_menu = on_back_to_menu
        self.on_test_race = on_test_race

        self.active_tab: str = "TRACK"  # "TRACK" or "DATABASE"

        self.track_editor = TrackEditor(screen_width, screen_height, on_test_race=self.on_test_race)
        self.database_editor = DatabaseEditor(
            screen_width, screen_height, exhibition_db_path=exhibition_db_path, career_db_path=career_db_path
        )

        self._init_fonts()

    def _init_fonts(self):
        self.font_btn = UITheme.get_font(11, bold=True)
        self.font_title = UITheme.get_font(12, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()
        self.track_editor.resize(width, height)
        self.database_editor.resize(width, height)

    def handle_event(self, event: pygame.event.Event):
        # Top Admin Hub Navigation Bar
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            btn_back = pygame.Rect(10, 10, 150, 28)
            tab_track = pygame.Rect(175, 10, 165, 28)
            tab_db = pygame.Rect(348, 10, 165, 28)

            if btn_back.collidepoint(mx, my):
                self.on_back_to_menu()
                return
            elif tab_track.collidepoint(mx, my):
                self.active_tab = "TRACK"
                return
            elif tab_db.collidepoint(mx, my):
                self.active_tab = "DATABASE"
                self.database_editor.reload_data()
                return

        # Delegate event to active sub-editor
        if self.active_tab == "TRACK":
            self.track_editor.handle_event(event)
        elif self.active_tab == "DATABASE":
            self.database_editor.handle_event(event)

    def update(self, dt: float):
        if self.active_tab == "DATABASE":
            self.database_editor.update(dt)

    def render(self, surface: pygame.Surface):
        surface.fill(UITheme.BG_DARK)

        # 1. Render Active Sub-Editor
        if self.active_tab == "TRACK":
            self.track_editor.render(surface)
        elif self.active_tab == "DATABASE":
            self.database_editor.render(surface)

        # 2. Render Global Admin Hub Top Bar
        top_bar = pygame.Rect(0, 0, self.width, 46)
        pygame.draw.rect(surface, (14, 18, 24), top_bar)
        pygame.draw.line(surface, UITheme.PANEL_BORDER, (0, 46), (self.width, 46), 1)

        # Back Button
        btn_back = pygame.Rect(10, 9, 150, 28)
        pygame.draw.rect(surface, (28, 36, 48), btn_back, border_radius=4)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, btn_back, width=1, border_radius=4)
        lbl_b = self.font_btn.render("< MAIN MENU", True, (255, 255, 255))
        surface.blit(lbl_b, (btn_back.x + (btn_back.width - lbl_b.get_width()) // 2, btn_back.y + 6))

        # Admin Mode Title / Badge
        t_badge = self.font_title.render("ADMIN & CREATOR SUITE", True, (255, 215, 0))
        surface.blit(t_badge, (self.width - t_badge.get_width() - 16, 14))

        # Tabs: TRACK DESIGNER & DATABASE EDITOR
        tab_track = pygame.Rect(175, 9, 165, 28)
        tab_db = pygame.Rect(348, 9, 165, 28)

        UITheme.draw_button(surface, tab_track, "TRACK DESIGNER", self.font_btn, is_active=(self.active_tab == "TRACK"))
        UITheme.draw_button(
            surface, tab_db, "DATABASE EDITOR", self.font_btn, is_active=(self.active_tab == "DATABASE")
        )
