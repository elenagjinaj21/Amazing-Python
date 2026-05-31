"""ASCII terminal renderer for A-Maze-ing mazes.

Renders the maze as Unicode box-drawing characters in the terminal,
with an optional solution path overlay and interactive controls.

Wall bitmask reference (same as the rest of the codebase):
    bit 0 (1) = North wall closed
    bit 1 (2) = East  wall closed
    bit 2 (4) = South wall closed
    bit 3 (8) = West  wall closed
"""
from __future__ import annotations

import os
import sys
from typing import Optional

# ── Display symbols ─────────────────────────────────────────────────────

# Corner / junction characters chosen so that adjacent walls line up cleanly.
# Key: (has_south, has_east) for the top-left corner of each 2×2 block.
_JUNCTIONS = {
    # (south, east)
    (False, False): "┘",
    (False, True): "└",
    (True, False): "┐",
    (True, True): "┌",
}

_H_WALL = "──"   # horizontal wall segment (two chars wide to match cell width)
_H_OPEN = "  "   # open horizontal passage
_V_WALL = "│"    # vertical wall segment
_V_OPEN = " "    # open vertical passage

_PATH_CHAR = "·"   # solution path dot
_ENTRY_CHAR = "S"   # entry marker
_EXIT_CHAR = "E"   # exit marker
_PATTERN_CHAR = "▓"   # 42-pattern filled cell

# ANSI colour codes (disabled automatically when stdout is not a tty)
_USE_COLOR = sys.stdout.isatty() and os.name != "nt" or (
    os.name == "nt" and "ANSICON" in os.environ
)


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _COL_WALL(t): return _c("35", t)      # magenta walls
def _COL_PATH(t): return _c("91", t)      # bright red path
def _COL_ENTRY(t): return _c("32;1", t)   # bold green entry
def _COL_EXIT(t): return _c("31;1", t)   # bold red exit
def _COL_PATTERN(t): return _c("95", t)     # bright magenta pattern


def _COL_HEADER(t): return _c("35;1", t)   # bold magenta header
def _COL_MUTED(t): return _c("2", t)      # dim muted text


# ── Path coordinate builder ─────────────────────────────────────────────

def _path_coords(
    entry: tuple[int, int],
    path: list[str],
) -> set[tuple[int, int]]:
    """Return the set of (x, y) cell coordinates visited by *path*."""
    coords: set[tuple[int, int]] = set()
    x, y = entry
    coords.add((x, y))
    for move in path:
        if move == "N":
            y -= 1
        elif move == "E":
            x += 1
        elif move == "S":
            y += 1
        else:
            x -= 1
        coords.add((x, y))
    return coords


# ── Core renderer ───────────────────────────────────────────────────────

def render_maze(
    maze: list[list[int]],
    entry: tuple[int, int],
    exit_: tuple[int, int],
    path: Optional[list[str]] = None,
    show_path: bool = True,
    pattern_cells: Optional[set[tuple[int, int]]] = None,
) -> str:
    """Render *maze* as a multi-line Unicode string.

    Each maze cell maps to a 2×1 character block (2 wide, 1 tall) in the
    cell body, with a 1-character border on the left and a 2-character
    border on the top.  The outer boundary is always fully closed.

    Args:
        maze: 2-D wall bitmask grid.
        entry: (x, y) entry cell.
        exit_: (x, y) exit cell.
        path: Solution path as direction letters; None means no path.
        show_path: If False the path overlay is hidden even if *path* is set.
        pattern_cells: Optional set of (x, y) cells of the 42 pattern.

    Returns:
        A single string (with embedded newlines) ready to print.
    """
    rows = len(maze)
    cols = len(maze[0]) if rows else 0
    ex, ey = entry
    xx, xy = exit_

    path_set: set[tuple[int, int]] = set()
    if show_path and path:
        path_set = _path_coords(entry, path)

    pat: set[tuple[int, int]] = pattern_cells or set()

    lines: list[str] = []

    # ── Top border row ──────────────────────────────────────────────────────
    top = "┌"
    for x in range(cols):
        top += _H_WALL
        top += ("┬" if x < cols - 1 else "┐")
    lines.append(_COL_WALL(top))

    # ── Cell rows ───────────────────────────────────────────────────────────
    for y in range(rows):
        # Cell body row
        body = _COL_WALL(_V_WALL)
        for x in range(cols):
            cell = maze[y][x]

            if (x, y) == (ex, ey):
                cell_str = _COL_ENTRY(f" {_ENTRY_CHAR}")
            elif (x, y) == (xx, xy):
                cell_str = _COL_EXIT(f" {_EXIT_CHAR}")
            elif (x, y) in pat:
                cell_str = _COL_PATTERN(_PATTERN_CHAR * 2)
            elif (x, y) in path_set:
                cell_str = _COL_PATH(f" {_PATH_CHAR}")
            else:
                cell_str = "  "

            # East wall
            if x < cols - 1:
                if cell & 2:  # East wall closed
                    east_sep = _COL_WALL(_V_WALL)
                else:
                    east_sep = " "
            else:
                east_sep = _COL_WALL(_V_WALL)

            body += cell_str + east_sep

        lines.append(body)

        # Bottom separator row (skip after last row → replaced by bottom
        # border)
        if y < rows - 1:
            sep = _COL_WALL("├")
            for x in range(cols):
                cell = maze[y][x]
                # South wall of this cell
                sep += _COL_WALL(_H_WALL) if (cell & 4) else _H_OPEN
                if x < cols - 1:
                    # Junction: look at south of (x,y), east of (x,y+1)
                    # Choose junction based on surrounding walls
                    # (top-right corner of junction square)
                    #   has south passage from (x,y)   → line going down
                    #   has east passage from (x+1,y)  → line going right
                    # We use a simplified 4-way junction
                    # south wall above = north here
                    # Build the correct T/cross/corner
                    junction = _junction_char(
                        north=bool(cell & 4),       # south wall of cell above
                        south=bool(maze[y + 1][x] & 4) if y +
                        1 < rows else True,
                        west=bool(cell & 2),
                        # east wall of cell to the left
                        east=bool(maze[y + 1][x] & 2),
                    )
                    sep += _COL_WALL(junction)
                else:
                    sep += _COL_WALL("┤")
            lines.append(sep)

    # ── Bottom border row ───────────────────────────────────────────────────
    bot = "└"
    for x in range(cols):
        bot += _H_WALL
        bot += ("┴" if x < cols - 1 else "┘")
    lines.append(_COL_WALL(bot))

    return "\n".join(lines)


def _junction_char(north: bool, south: bool, west: bool, east: bool) -> str:
    """Return the Unicode box-drawing character for a 4-way junction.

    Args:
        north: True if there is a wall segment going north.
        south: True if there is a wall segment going south.
        west:  True if there is a wall segment going west.
        east:  True if there is a wall segment going east.
    """
    # Map all 16 combinations
    _MAP = {
        (False, False, False, False): " ",
        (True, False, False, False): "╵",
        (False, True, False, False): "╷",
        (True, True, False, False): "│",
        (False, False, True, False): "╴",
        (True, False, True, False): "┘",
        (False, True, True, False): "┐",
        (True, True, True, False): "┤",
        (False, False, False, True): "╶",
        (True, False, False, True): "└",
        (False, True, False, True): "┌",
        (True, True, False, True): "├",
        (False, False, True, True): "─",
        (True, False, True, True): "┴",
        (False, True, True, True): "┬",
        (True, True, True, True): "┼",
    }
    return _MAP[(north, south, west, east)]


# ── Interactive ASCII session ───────────────────────────────────────────

class MazeASCII:
    """Interactive ASCII terminal session for the maze.

    Mirrors the controls available in the Pygame GUI (regenerate, toggle path,
    quit) adapted for a terminal environment.
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
        self.show_path = True
        self._pattern_cells: set[tuple[int, int]] = set()
        self._update_pattern_cells()

    # ── Internal helpers ────────────────────────────────────────────────────

    def _update_pattern_cells(self) -> None:
        self._pattern_cells = set()
        if not self.config.get("DRAW_42", False):
            return
        from maze.pattern import place_42_cells
        cols = len(self.maze[0]) if self.maze else 0
        rows = len(self.maze)
        cells = place_42_cells(cols, rows)
        if cells:
            self._pattern_cells = set(cells)

    def _regenerate(self) -> None:
        from maze.generator import MazeGenerator
        from maze.solver import solve_bfs
        from maze.writer import write_output

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
        self._update_pattern_cells()

        try:
            write_output(
                self.maze,
                self.config["OUTPUT_FILE"],
                self.entry,
                self.exit_,
                self.path,
            )
        except OSError as exc:
            print(f"Warning: could not write output file: {exc}")

    def _print_frame(self) -> None:
        cols = len(self.maze[0]) if self.maze else 0
        rows = len(self.maze)
        alg = self.config.get("ALGORITHM", "wilson").upper()
        perfect = "yes" if self.config.get("PERFECT", False) else "no"
        path_state = "shown" if self.show_path else "hidden"

        print()
        print(_COL_HEADER("  ♥  A-Maze-ing  ♥"))
        print(_COL_MUTED(
            f"  {cols}×{rows}  │  {alg}  │  perfect: {perfect}"
            f"  │  path: {path_state} ({len(self.path)} steps)"
        ))
        print()
        print(render_maze(
            self.maze,
            self.entry,
            self.exit_,
            path=self.path,
            show_path=self.show_path,
            pattern_cells=self._pattern_cells,
        ))
        print()
        print(_COL_MUTED(
            "  [1] Regenerate   [2] Toggle path   [q] Quit"
        ))
        print()

    # ── Public API ──────────────────────────────────────────────────────────

    def run(self) -> None:
        """Enter the interactive terminal loop."""
        self._print_frame()

        while True:
            try:
                choice = input("  > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if choice in ("q", "quit", "exit", "7"):
                print("  Bye! ♥")
                break
            elif choice in ("1",):
                print("  Regenerating…")
                self._regenerate()
                self._print_frame()
            elif choice in ("2",):
                self.show_path = not self.show_path
                self._print_frame()
            else:
                print(_COL_MUTED("  Unknown command. Use 1 / 2 / q."))
