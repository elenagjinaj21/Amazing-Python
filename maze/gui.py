"""Maze GUI – pink-themed pygame interface for A-Maze-ing.

Replaces the original tkinter implementation with pygame,
which can be installed without sudo:
    pip install pygame --user
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import pygame

from maze.generator import MazeGenerator
from maze.solver import solve_bfs
from maze.writer import write_output

# ── Layout constants ────────────────────────────────────────────────────
WIN_W = 1800     # fixed window width
WIN_H = 1100     # fixed window height

CELL_MIN = 55    # minimum pixels per maze cell
CELL_MAX = 80    # maximum pixels per maze cell
WALL_W = 2       # wall line width in pixels
BORDER = 12      # outer canvas padding
PAD = 4          # general widget spacing

HEADER_H = 54    # header panel height
CTRL_H = 74      # controls area height
STATUS_H = 26    # status bar height

BTN_W = 132      # button width
BTN_H = 32       # button height
BTN_RADIUS = 6   # button corner radius

KITTY_IMG_SIZE = 200  # target size of the corner kitty image (px)

# ── Pink colour palette ─────────────────────────────────────────────────
WIN_BG = (252, 228, 236)   # window background – blush
HEADER_BG = (248, 187, 208)   # header panel – soft pink
CTRL_BG = (252, 228, 236)   # control strip background
CANVAS_BG_DEF = "#fff0f5"
WALL_COL_DEF = "#ad1457"
PATH_COL_DEF = "#e91e63"
ENTRY_COL = (165, 214, 167)   # mint green
EXIT_COL = (239, 154, 154)   # salmon
PAT42_COL_DEF = "#f06292"
STATUS_BG = (244, 143, 177)   # status bar – pink
ACCENT = (194, 24, 91)   # primary button – dark pink
ACCENT_HOVER = (233, 30, 99)
BTN_SEC = (136, 14, 79)
BTN_SEC_HOVER = (173, 20, 87)
QUIT_COL = (74, 20, 140)
QUIT_HOVER = (106, 27, 154)
BTN_FG = (255, 255, 255)
TEXT_DARK = (74, 0, 25)
TEXT_MUTED = (136, 14, 79)
BORDER_COL = (244, 143, 177)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string like '#ad1457' to an (R, G, B) tuple."""
    h = hex_color.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _blend(col_a: str, col_b: str, t: float) -> tuple[int, int, int]:
    """Linearly interpolate between two hex colours."""
    try:
        ra, ga, ba = _hex_to_rgb(col_a)
        rb, gb, bb = _hex_to_rgb(col_b)
        return (
            int(ra + (rb - ra) * t),
            int(ga + (gb - ga) * t),
            int(ba + (bb - ba) * t),
        )
    except Exception:
        return _hex_to_rgb(col_a)


def _draw_rounded_rect(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    radius: int = 6,
) -> None:
    """Draw a filled rounded rectangle."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)


class Button:
    """A simple clickable button with hover effect."""

    def __init__(
        self,
        text: str,
        rect: pygame.Rect,
        color: tuple[int, int, int],
        hover_color: tuple[int, int, int],
        font: pygame.font.Font,
    ) -> None:
        self.text = text
        self.rect = rect
        self.color = color
        self.hover_color = hover_color
        self.font = font
        self.hovered = False

    def draw(self, surface: pygame.Surface) -> None:
        col = self.hover_color if self.hovered else self.color
        _draw_rounded_rect(surface, col, self.rect, BTN_RADIUS)
        label = self.font.render(self.text, True, BTN_FG)
        lx = self.rect.centerx - label.get_width() // 2
        ly = self.rect.centery - label.get_height() // 2
        surface.blit(label, (lx, ly))

    def update(self, mouse_pos: tuple[int, int]) -> None:
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class ColorPicker:
    """A minimal in-window HSV colour picker shown as an overlay."""

    def __init__(self, surface: pygame.Surface,
                 font: pygame.font.Font) -> None:
        self.surface = surface
        self.font = font
        self.active = False
        self.result: Optional[str] = None
        self._done = False
        self._cancel = False

        W = surface.get_width()
        H = surface.get_height()
        pw, ph = 320, 260
        self.panel = pygame.Rect((W - pw) // 2, (H - ph) // 2, pw, ph)

        # Hue bar
        self.hue_rect = pygame.Rect(
            self.panel.x + 20, self.panel.y + 40, 280, 24)
        # SV square
        self.sv_rect = pygame.Rect(
            self.panel.x + 20, self.panel.y + 80, 180, 130)
        # Preview swatch
        self.preview_rect = pygame.Rect(
            self.panel.x + 210, self.panel.y + 80, 90, 60)
        # OK button
        self.ok_btn = pygame.Rect(
            self.panel.x + 210, self.panel.y + 155, 90, 30)
        # Cancel
        self.cancel_btn = pygame.Rect(
            self.panel.x + 210, self.panel.y + 195, 90, 30)

        self._hue = 0.0        # 0-1
        self._sat = 0.8        # 0-1
        self._val = 0.8        # 0-1
        self._dragging_hue = False
        self._dragging_sv = False

        # Pre-build hue bar surface (static)
        self._hue_surf = self._make_hue_surf()
        self._sv_surf: Optional[pygame.Surface] = None

    # ── surface builders ────────────────────────────────────────────────────

    def _make_hue_surf(self) -> pygame.Surface:
        w, h = self.hue_rect.width, self.hue_rect.height
        surf = pygame.Surface((w, h))
        for px in range(w):
            hue = px / w
            col = pygame.Color(0)
            col.hsva = (hue * 360, 100, 100, 100)
            pygame.draw.line(surf, col, (px, 0), (px, h - 1))
        return surf

    def _make_sv_surf(self) -> pygame.Surface:
        w, h = self.sv_rect.width, self.sv_rect.height
        surf = pygame.Surface((w, h))
        for py in range(h):
            for px in range(w):
                s = px / w
                v = 1.0 - py / h
                col = pygame.Color(0)
                col.hsva = (self._hue * 360, s * 100, v * 100, 100)
                surf.set_at((px, py), col)
        return surf

    def _current_color_hex(self) -> str:
        col = pygame.Color(0)
        col.hsva = (self._hue * 360, self._sat * 100, self._val * 100, 100)
        return f"#{col.r:02x}{col.g:02x}{col.b:02x}"

    # ── public API ──────────────────────────────────────────────────────────

    def open(self, current_hex: str) -> None:
        try:
            r, g, b = _hex_to_rgb(current_hex)
            col = pygame.Color(r, g, b)
            h, s, v, _ = col.hsva
            self._hue = h / 360
            self._sat = s / 100
            self._val = v / 100
        except Exception:
            self._hue, self._sat, self._val = 0.0, 0.8, 0.8
        self._sv_surf = self._make_sv_surf()
        self.active = True
        self.result = None
        self._done = False
        self._cancel = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.active:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.ok_btn.collidepoint(event.pos):
                self.result = self._current_color_hex()
                self.active = False
                self._done = True
            elif self.cancel_btn.collidepoint(event.pos):
                self.result = None
                self.active = False
                self._cancel = True
            elif self.hue_rect.collidepoint(event.pos):
                self._dragging_hue = True
                self._update_hue(event.pos[0])
            elif self.sv_rect.collidepoint(event.pos):
                self._dragging_sv = True
                self._update_sv(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._dragging_hue = False
            self._dragging_sv = False
        elif event.type == pygame.MOUSEMOTION:
            if self._dragging_hue:
                self._update_hue(event.pos[0])
            elif self._dragging_sv:
                self._update_sv(event.pos)

    def _update_hue(self, mx: int) -> None:
        self._hue = max(
            0.0, min(
                1.0, (mx - self.hue_rect.x) / self.hue_rect.width))
        self._sv_surf = self._make_sv_surf()

    def _update_sv(self, pos: tuple[int, int]) -> None:
        mx, my = pos
        self._sat = max(
            0.0, min(
                1.0, (mx - self.sv_rect.x) / self.sv_rect.width))
        self._val = max(
            0.0, min(1.0, 1.0 - (my - self.sv_rect.y) / self.sv_rect.height))

    def draw(self) -> None:
        if not self.active:
            return
        # Dim background
        overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        self.surface.blit(overlay, (0, 0))

        # Panel
        pygame.draw.rect(self.surface, (250, 230, 240),
                         self.panel, border_radius=10)
        pygame.draw.rect(self.surface, (200, 100, 150),
                         self.panel, 2, border_radius=10)

        # Title
        title = self.font.render("Pick a colour", True, TEXT_DARK)
        self.surface.blit(title, (self.panel.x + 20, self.panel.y + 10))

        # Hue bar
        self.surface.blit(self._hue_surf, self.hue_rect)
        hx = int(self.hue_rect.x + self._hue * self.hue_rect.width)
        pygame.draw.rect(self.surface, (255, 255, 255), pygame.Rect(
            hx - 2, self.hue_rect.y - 2, 4, self.hue_rect.height + 4), 2)

        # SV square
        if self._sv_surf:
            self.surface.blit(self._sv_surf, self.sv_rect)
        sx = int(self.sv_rect.x + self._sat * self.sv_rect.width)
        sy = int(self.sv_rect.y + (1 - self._val) * self.sv_rect.height)
        pygame.draw.circle(self.surface, (255, 255, 255), (sx, sy), 5, 2)

        # Preview swatch
        preview_col = _hex_to_rgb(self._current_color_hex())
        pygame.draw.rect(
            self.surface,
            preview_col,
            self.preview_rect,
            border_radius=4)
        pygame.draw.rect(self.surface, (150, 80, 120),
                         self.preview_rect, 1, border_radius=4)

        # Hex label under preview
        hex_label = self.font.render(
            self._current_color_hex(), True, TEXT_DARK)
        self.surface.blit(
            hex_label,
            (self.preview_rect.x,
             self.preview_rect.bottom + 4))

        # OK / Cancel
        pygame.draw.rect(self.surface, ACCENT, self.ok_btn, border_radius=5)
        ok_t = self.font.render("OK", True, BTN_FG)
        self.surface.blit(ok_t, (self.ok_btn.centerx - ok_t.get_width() // 2,
                                 self.ok_btn.centery - ok_t.get_height() // 2))

        pygame.draw.rect(
            self.surface,
            BTN_SEC,
            self.cancel_btn,
            border_radius=5)
        cn_t = self.font.render("Cancel", True, BTN_FG)
        self.surface.blit(
            cn_t,
            (self.cancel_btn.centerx -
             cn_t.get_width() //
             2,
             self.cancel_btn.centery -
             cn_t.get_height() //
             2))


class MazeGUI:
    """Pygame GUI for the A-Maze-ing maze generator.

    Displays the generated maze with optional solution path overlay,
    user-controlled colour schemes, and all subject-required interactions.
    """

    def __init__(
        self,
        maze: list[list[int]],
        entry: tuple[int, int],
        exit_: tuple[int, int],
        path: list[str],
        config: dict,  # type: ignore[type-arg]
    ) -> None:
        self.maze = maze
        self.entry = entry
        self.exit_ = exit_
        self.path = path
        self.config = config

        self.show_path: bool = True
        self.wall_color: str = config.get("WALL_COLOR", WALL_COL_DEF)
        self.canvas_bg: str = config.get("CANVAS_BG", CANVAS_BG_DEF)
        self.path_color: str = config.get("PATH_COLOR", PATH_COL_DEF)
        self.pattern_color: str = config.get("COLOR_42") or PAT42_COL_DEF
        self.draw_42: bool = bool(config.get("DRAW_42", False))
        self.pattern_cells: list[tuple[int, int]] = []
        # 0=top-right, 1=top-left, 2=bottom-right, 3=bottom-left
        self.image_position: int = 0

        self._custom_img: Optional[pygame.Surface] = None
        self._badge_img: Optional[pygame.Surface] = None

        self._status = "Ready"

        pygame.init()
        pygame.font.init()

        cols = len(self.maze[0]) if self.maze else 0
        rows = len(self.maze)

        # Compute a cell size that fills ~65 % of the window width, clamped to
        # [CELL_MIN, CELL_MAX]
        _maze_area_h = WIN_H - HEADER_H - CTRL_H - STATUS_H
        _cell_from_w = (WIN_W * 0.65 - 2 * BORDER) / \
            cols if cols else float(CELL_MAX)
        _cell_from_h = (_maze_area_h - 2 * BORDER) / \
            rows if rows else float(CELL_MAX)
        self._cell = int(
            max(CELL_MIN, min(CELL_MAX, min(_cell_from_w, _cell_from_h))))

        self._maze_w = cols * self._cell + 2 * BORDER
        self._maze_h = rows * self._cell + 2 * BORDER

        self._win_w = WIN_W
        self._win_h = WIN_H

        # Center the maze horizontally; center vertically in the space between
        # header and controls
        self._maze_x = (WIN_W - self._maze_w) // 2
        self._maze_y = HEADER_H + (_maze_area_h - self._maze_h) // 2

        self._screen = pygame.display.set_mode((self._win_w, self._win_h))
        pygame.display.set_caption("A-Maze-ing <3")

        self._font_title = pygame.font.SysFont(
            "segoeui,dejavusans,sans", 22, bold=True)
        self._font_btn = pygame.font.SysFont(
            "segoeui,dejavusans,sans", 12, bold=True)
        self._font_small = pygame.font.SysFont("segoeui,dejavusans,sans", 11)
        self._font_status = pygame.font.SysFont("segoeui,dejavusans,sans", 11)

        self._color_picker = ColorPicker(self._screen, self._font_btn)
        self._pending_color_target: Optional[str] = None

        self._load_custom_image(config.get("CUSTOM_IMAGE"))
        self._build_buttons()
        self.update_pattern_cells()

    # ── Image loading ───────────────────────────────────────────────────────

    def _load_custom_image(self, custom_path: Optional[str]) -> None:
        """Load the custom PNG image scaled to fit the side kitty panel."""
        candidates: list[str] = []
        if custom_path:
            candidates.append(custom_path)
            candidates.append(os.path.join(os.getcwd(), custom_path))
        here = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(here)
        candidates.append(os.path.join(project_root, "hellokitty.png"))
        candidates.append(os.path.join(os.getcwd(), "hellokitty.png"))

        for p in candidates:
            if p and os.path.isfile(p):
                try:
                    surf = pygame.image.load(p).convert_alpha()
                    ow, oh = surf.get_size()

                    # Corner image: fit within KITTY_IMG_SIZE × KITTY_IMG_SIZE
                    scale = min(KITTY_IMG_SIZE / ow, KITTY_IMG_SIZE / oh)
                    nw = max(1, int(ow * scale))
                    nh = max(1, int(oh * scale))
                    self._custom_img = pygame.transform.smoothscale(
                        surf, (nw, nh))

                    # Small badge for the header: ~36px tall
                    badge_h = 36
                    bscale = badge_h / oh
                    bw = max(1, int(ow * bscale))
                    self._badge_img = pygame.transform.smoothscale(
                        surf, (bw, badge_h))

                    print(f"Image loaded: {p} ({ow}x{oh} → panel {nw}x{nh})")
                    return
                except Exception as exc:
                    print(f"Warning: could not load image {p}: {exc}")

    # ── Button layout ───────────────────────────────────────────────────────

    def _build_buttons(self) -> None:
        ctrl_y = WIN_H - STATUS_H - CTRL_H
        specs = [
            ("1. Regenerate", self._cb_regenerate, ACCENT, ACCENT_HOVER),
            ("2. Toggle Path", self._cb_toggle_path, BTN_SEC, BTN_SEC_HOVER),
            ("3. Wall Color", self._cb_wall_color, BTN_SEC, BTN_SEC_HOVER),
            ("4. 42 Color", self._cb_pattern_color, BTN_SEC, BTN_SEC_HOVER),
            ("5. BG Color", self._cb_bg_color, BTN_SEC, BTN_SEC_HOVER),
            ("6. Find Kitty", self._cb_cycle_image, BTN_SEC, BTN_SEC_HOVER),
            ("7. Quit", self._cb_quit, QUIT_COL, QUIT_HOVER),
        ]
        self._buttons: list[tuple[Button, object]] = []
        x = 10
        y = ctrl_y + 10
        for label, cb, col, hov in specs:
            rect = pygame.Rect(x, y, BTN_W, BTN_H)
            btn = Button(label, rect, col, hov, self._font_btn)
            self._buttons.append((btn, cb))
            x += BTN_W + 8

    # ── Drawing helpers ─────────────────────────────────────────────────────

    def _draw_header(self) -> None:
        pygame.draw.rect(
            self._screen, HEADER_BG, pygame.Rect(
                0, 0, self._win_w, HEADER_H))
        title = self._font_title.render("A-Maze-ing ♥", True, TEXT_DARK)
        self._screen.blit(
            title, (BORDER + 4, (HEADER_H - title.get_height()) // 2))
        if self._badge_img:
            bx = self._win_w - self._badge_img.get_width() - BORDER - 4
            by = (HEADER_H - self._badge_img.get_height()) // 2
            self._screen.blit(self._badge_img, (bx, by))

    def _draw_maze_canvas(self) -> None:
        maze_x = self._maze_x
        maze_y = self._maze_y
        bg = _hex_to_rgb(self.canvas_bg)
        wall_col = _hex_to_rgb(self.wall_color)
        pat_col = _hex_to_rgb(self.pattern_color)

        # Canvas background
        pygame.draw.rect(
            self._screen,
            bg,
            pygame.Rect(
                maze_x,
                maze_y,
                self._maze_w,
                self._maze_h))
        pygame.draw.rect(
            self._screen,
            BORDER_COL,
            pygame.Rect(
                maze_x,
                maze_y,
                self._maze_w,
                self._maze_h),
            2)

        # Pattern cells (42)
        for (px, py) in self.pattern_cells:
            rx = maze_x + px * self._cell + BORDER
            ry = maze_y + py * self._cell + BORDER
            pygame.draw.rect(self._screen, pat_col,
                             pygame.Rect(rx, ry, self._cell, self._cell))

        # Walls
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                x1 = maze_x + x * self._cell + BORDER
                y1 = maze_y + y * self._cell + BORDER
                x2 = x1 + self._cell
                y2 = y1 + self._cell
                if cell & 1:  # North
                    pygame.draw.line(
                        self._screen, wall_col, (x1, y1), (x2, y1), WALL_W)
                if cell & 2:  # East
                    pygame.draw.line(
                        self._screen, wall_col, (x2, y1), (x2, y2), WALL_W)
                if cell & 4:  # South
                    pygame.draw.line(
                        self._screen, wall_col, (x1, y2), (x2, y2), WALL_W)
                if cell & 8:  # West
                    pygame.draw.line(
                        self._screen, wall_col, (x1, y1), (x1, y2), WALL_W)

        # Solution path
        if self.show_path and self.path:
            self._draw_path(maze_x, maze_y)

        # Entry / exit markers
        self._draw_entry(maze_x, maze_y)
        self._draw_exit(maze_x, maze_y)

    def _draw_path(self, maze_x: int, maze_y: int) -> None:
        x, y = self.entry
        c = self._cell
        pts: list[tuple[int, int]] = [(
            maze_x + x * c + BORDER + c // 2,
            maze_y + y * c + BORDER + c // 2,
        )]
        for move in self.path:
            if move == "N":
                y -= 1
            elif move == "E":
                x += 1
            elif move == "S":
                y += 1
            else:
                x -= 1
            pts.append((
                maze_x + x * c + BORDER + c // 2,
                maze_y + y * c + BORDER + c // 2,
            ))
        if len(pts) >= 2:
            glow_col = _blend(self.path_color, "#ffffff", 0.5)
            pygame.draw.lines(self._screen, glow_col, False, pts, WALL_W + 6)
            pygame.draw.lines(self._screen, _hex_to_rgb(self.path_color),
                              False, pts, WALL_W + 2)

    def _draw_entry(self, maze_x: int, maze_y: int) -> None:
        ex, ey = self.entry
        c = self._cell
        cx = maze_x + ex * c + BORDER + c // 2
        cy = maze_y + ey * c + BORDER + c // 2
        r = c // 2 - 3
        pygame.draw.circle(self._screen, ENTRY_COL, (cx, cy), r)
        pygame.draw.circle(self._screen, (46, 125, 50), (cx, cy), r, 2)
        s_label = self._font_small.render("S", True, (27, 94, 32))
        self._screen.blit(s_label, (cx - s_label.get_width() // 2,
                                    cy - s_label.get_height() // 2))

    def _draw_exit(self, maze_x: int, maze_y: int) -> None:
        xx, xy = self.exit_
        c = self._cell
        x1 = maze_x + xx * c + BORDER + 3
        y1 = maze_y + xy * c + BORDER + 3
        x2 = x1 + c - 6
        y2 = y1 + c - 6
        pygame.draw.rect(
            self._screen, EXIT_COL, pygame.Rect(
                x1, y1, x2 - x1, y2 - y1))
        pygame.draw.rect(self._screen, (183, 28, 28),
                         pygame.Rect(x1, y1, x2 - x1, y2 - y1), 2)
        e_label = self._font_small.render("E", True, (127, 0, 0))
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        self._screen.blit(e_label, (cx - e_label.get_width() // 2,
                                    cy - e_label.get_height() // 2))

    def _draw_kitty_corners(self) -> None:
        """Draw the kitty image in one of four corners outside the maze area.

        The image never overlaps the maze; it sits in the open space to the
        left or right of the centred maze canvas.  'Find Kitty' cycles through
        top-left → top-right → bottom-left → bottom-right.
        """
        if self._custom_img is None:
            return

        iw, ih = self._custom_img.get_size()
        mx = self._maze_x
        my = self._maze_y
        mw = self._maze_w
        mh = self._maze_h
        pad = 12

        # 4 corner anchor positions outside the maze rectangle
        # 0 = top-left,  1 = top-right,  2 = bottom-left,  3 = bottom-right
        positions = [
            (mx - iw - pad, my),               # top-left
            (mx + mw + pad, my),               # top-right
            (mx - iw - pad, my + mh - ih),     # bottom-left
            (mx + mw + pad, my + mh - ih),     # bottom-right
        ]
        sx, sy = positions[self.image_position]

        # Clamp to safe window area (stay inside header and above controls)
        ctrl_top = WIN_H - STATUS_H - CTRL_H
        sx = max(0, min(sx, WIN_W - iw))
        sy = max(HEADER_H, min(sy, ctrl_top - ih))

        # Soft pink halo behind the image
        halo = pygame.Rect(sx - 6, sy - 6, iw + 12, ih + 12)
        pygame.draw.rect(self._screen, HEADER_BG, halo, border_radius=12)

        self._screen.blit(self._custom_img, (sx, sy))

    def _draw_controls(self) -> None:
        ctrl_y = WIN_H - STATUS_H - CTRL_H
        pygame.draw.rect(self._screen, WIN_BG,
                         pygame.Rect(0, ctrl_y, self._win_w, CTRL_H))
        for btn, _ in self._buttons:
            btn.draw(self._screen)
        # Legend
        items = [
            ("Wall", self.wall_color, "line"),
            ("Path", self.path_color, "line"),
            ("Entry", "#a5d6a7", "dot"),
            ("Exit", "#ef9a9a", "rect"),
            ("42", self.pattern_color, "rect"),
        ]
        lx = 10
        ly = ctrl_y + BTN_H + 18
        for name, color_hex, shape in items:
            col = _hex_to_rgb(color_hex)
            if shape == "line":
                pygame.draw.line(
                    self._screen, col, (lx, ly + 7), (lx + 18, ly + 7), 3)
            elif shape == "dot":
                pygame.draw.circle(self._screen, col, (lx + 9, ly + 7), 7)
            else:
                pygame.draw.rect(
                    self._screen, col, pygame.Rect(
                        lx, ly + 2, 18, 10))
            lbl = self._font_small.render(name, True, TEXT_MUTED)
            self._screen.blit(lbl, (lx + 22, ly + 7 - lbl.get_height() // 2))
            lx += 22 + lbl.get_width() + 14

    def _draw_statusbar(self) -> None:
        sy = self._win_h - STATUS_H
        pygame.draw.rect(self._screen, STATUS_BG,
                         pygame.Rect(0, sy, self._win_w, STATUS_H))
        lbl = self._font_status.render(self._status, True, TEXT_DARK)
        self._screen.blit(
            lbl, (BORDER + 4, sy + (STATUS_H - lbl.get_height()) // 2))

    def _update_status(self) -> None:
        cols = len(self.maze[0]) if self.maze else 0
        rows = len(self.maze)
        alg = self.config.get("ALGORITHM", "wilson").upper()
        perfect = "YES" if self.config.get("PERFECT", False) else "NO"
        path_state = "shown" if self.show_path else "hidden"
        self._status = (
            f"  {cols}×{rows}  |  {alg}  "
            f"|  perfect: {perfect}  "
            f"|  path: {path_state} ({len(self.path)} steps)"
        )

    def draw(self) -> None:
        """Redraw the entire window."""
        self._screen.fill(WIN_BG)
        self._draw_header()
        self._draw_maze_canvas()
        self._draw_kitty_corners()
        self._draw_controls()
        self._update_status()
        self._draw_statusbar()
        if self._color_picker.active:
            self._color_picker.draw()
        pygame.display.flip()

    # ── Button callbacks ────────────────────────────────────────────────────

    def _cb_toggle_path(self) -> None:
        self.show_path = not self.show_path

    def _cb_regenerate(self) -> None:
        gen = MazeGenerator(
            width=self.config["WIDTH"],
            height=self.config["HEIGHT"],
            seed=None,
            algorithm=self.config.get("ALGORITHM", "wilson"),
            perfect=self.config.get("PERFECT", False),
            draw_42=self.config.get("DRAW_42", False),
            entry=self.entry,
            exit_=self.exit_,
        )
        new_maze = gen.generate()
        new_path = solve_bfs(new_maze, self.entry, self.exit_)
        for _ in range(20):
            if new_path:
                break
            new_maze = gen.generate()
            new_path = solve_bfs(new_maze, self.entry, self.exit_)
        self.maze = new_maze
        self.path = new_path
        self.update_pattern_cells()
        try:
            write_output(
                self.maze, self.config["OUTPUT_FILE"],
                self.entry, self.exit_, self.path,
            )
        except OSError as exc:
            print(f"Warning: could not write output file: {exc}")

    def _cb_wall_color(self) -> None:
        self._pending_color_target = "wall"
        self._color_picker.open(self.wall_color)

    def _cb_pattern_color(self) -> None:
        self._pending_color_target = "pattern"
        self._color_picker.open(self.pattern_color)

    def _cb_bg_color(self) -> None:
        self._pending_color_target = "bg"
        self._color_picker.open(self.canvas_bg)

    def _cb_cycle_image(self) -> None:
        if self._custom_img is None:
            return
        self.image_position = (self.image_position + 1) % 4
        positions = [
            "top-left", "top-right", "bottom-left",
            "bottom-right"]
        msg = f"Kitty moved to {positions[self.image_position]} corner!"
        self._status = msg

    def _cb_quit(self) -> None:
        pygame.quit()
        sys.exit(0)

    # ── Pattern cells ───────────────────────────────────────────────────────

    def update_pattern_cells(self) -> None:
        self.pattern_cells = []
        if not self.draw_42:
            return
        from maze.pattern import place_42_cells
        cells = place_42_cells(
            len(self.maze[0]) if self.maze else 0, len(self.maze))
        if cells:
            self.pattern_cells = list(cells)

    # ── Main loop ───────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the pygame main event loop."""
        clock = pygame.time.Clock()
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for btn, _ in self._buttons:
                btn.update(mouse_pos)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

                if self._color_picker.active:
                    self._color_picker.handle_event(event)
                    if not self._color_picker.active:
                        color = self._color_picker.result
                        if color:
                            if self._pending_color_target == "wall":
                                self.wall_color = color
                            elif self._pending_color_target == "pattern":
                                self.pattern_color = color
                            elif self._pending_color_target == "bg":
                                self.canvas_bg = color
                        self._pending_color_target = None
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit(0)
                    elif event.key in (pygame.K_1, pygame.K_KP1):
                        self._cb_regenerate()
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        self._cb_toggle_path()
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        self._cb_wall_color()
                    elif event.key in (pygame.K_4, pygame.K_KP4):
                        self._cb_pattern_color()
                    elif event.key in (pygame.K_5, pygame.K_KP5):
                        self._cb_bg_color()
                    elif event.key in (pygame.K_6, pygame.K_KP6):
                        self._cb_cycle_image()
                    elif event.key in (pygame.K_7, pygame.K_KP7):
                        self._cb_quit()

                for btn, cb in self._buttons:
                    if btn.is_clicked(event):
                        cb()  # type: ignore[operator]
                        break

            self.draw()
            clock.tick(60)
