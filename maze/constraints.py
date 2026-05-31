"""Constraint helpers: embed 42 pattern and enforce corridor-width limits."""
from __future__ import annotations

from typing import Callable

from maze.pattern import apply_pattern, place_42_cells
from maze.perfect import entry_exit_has_unique_path


def try_embed_42(
    maze: list[list[int]],
    width: int,
    height: int,
) -> bool:
    """Attempt to embed the '42' pattern in the maze in-place.

    Prints a console error if the maze is too small to fit the pattern.

    Args:
        maze: 2-D maze grid (modified in-place on success).
        width: Maze width in cells.
        height: Maze height in cells.

    Returns:
        True if the pattern was embedded; False if the maze is too small.
    """
    cells = place_42_cells(width, height)
    if cells is None:
        print("Error: maze size too small to display '42' pattern.")
        return False
    apply_pattern(maze, cells)
    return True


def check_wall_coherence(maze: list[list[int]]) -> bool:
    """Verify that neighbouring cells agree on shared walls.

    A cell's East wall must equal its east neighbour's West wall, and
    a cell's South wall must equal its south neighbour's North wall.

    Args:
        maze: 2-D maze grid.

    Returns:
        True if the maze is internally consistent, False otherwise.
    """
    h = len(maze)
    w = len(maze[0]) if h else 0
    for y in range(h):
        for x in range(w):
            cell = maze[y][x]
            # Check East <-> West coherence
            if x + 1 < w:
                east_has_wall = bool(cell & 2)
                neighbour_has_west = bool(maze[y][x + 1] & 8)
                if east_has_wall != neighbour_has_west:
                    return False
            # Check South <-> North coherence
            if y + 1 < h:
                south_has_wall = bool(cell & 4)
                neighbour_has_north = bool(maze[y + 1][x] & 1)
                if south_has_wall != neighbour_has_north:
                    return False
    return True


def check_no_large_open_areas(maze: list[list[int]]) -> bool:
    """Verify that no 3×3 (or larger) fully open area exists in the maze.

    The subject forbids corridors wider than 2 cells. A 3×3 open area
    means a 3×3 block where every internal wall is absent.

    Args:
        maze: 2-D maze grid.

    Returns:
        True if no 3×3 open block is found, False otherwise.
    """
    h = len(maze)
    w = len(maze[0]) if h else 0
    if w < 3 or h < 3:
        return True

    for y in range(h - 2):
        for x in range(w - 2):
            # Check if cells (x..x+2, y..y+2) form a 3×3 open area
            open_block = True
            for by in range(y, y + 3):
                for bx in range(x, x + 3):
                    cell = maze[by][bx]
                    # East wall must be open within block
                    if bx < x + 2 and (cell & 2):
                        open_block = False
                        break
                    # South wall must be open within block
                    if by < y + 2 and (cell & 4):
                        open_block = False
                        break
                if not open_block:
                    break
            if open_block:
                return False
    return True


def enforce_perfect_constraints(
    generator_callable: Callable[[], list[list[int]]],
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
    draw_42: bool,
    max_tries: int = 200,
) -> list[list[int]]:
    """Regenerate until the maze satisfies the perfect-maze condition.

    In perfect mode the algorithm already produces spanning-tree mazes,
    so this is mainly for robustness when the '42' pattern is embedded
    (pattern insertion can create isolated cells).

    Args:
        generator_callable: Zero-argument callable returning a fresh maze.
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Entry cell coordinates.
        exit_: Exit cell coordinates.
        draw_42: Whether to embed the '42' pattern before checking.
        max_tries: Maximum generation attempts before returning best result.

    Returns:
        A maze satisfying the perfect constraint, or the last generated maze.
    """
    last: list[list[int]] = generator_callable()
    _warned = False
    for _ in range(max_tries):
        maze = generator_callable()
        if draw_42:
            from maze.pattern import place_42_cells, apply_pattern
            cells = place_42_cells(width, height)
            if cells is None:
                if not _warned:
                    print(
                        "Error: maze too small for '42' pattern.")
                    _warned = True
                # Pattern won't fit – check perfect condition without it
            else:
                apply_pattern(maze, cells)
        if entry_exit_has_unique_path(maze, entry, exit_):
            return maze
        last = maze
    return last
