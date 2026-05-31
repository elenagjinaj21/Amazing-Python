"""42 pattern definition and placement utilities."""
from __future__ import annotations

from typing import Iterable, Optional

FULL_CELL = 15  # All 4 walls closed: N|E|S|W = 1|2|4|8


def _bitmap_42() -> tuple[tuple[int, int], ...]:
    """Return the (col, row) offsets that spell '42' as a bitmap font.

    Returns:
        Sorted tuple of (x, y) pixel offsets forming the '42' glyph.
    """
    filled = {
        # Digit "4" (columns 0-3, rows 0-6)
        (0, 0), (3, 0),
        (0, 1), (3, 1),
        (0, 2), (3, 2),
        (0, 3), (1, 3), (2, 3), (3, 3),
        (3, 4),
        (3, 5),
        (3, 6),
        # Digit "2" (columns 5-9, rows 0-6)
        (5, 0), (6, 0), (7, 0), (8, 0), (9, 0),
        (9, 1),
        (9, 2),
        (5, 3), (6, 3), (7, 3), (8, 3), (9, 3),
        (5, 4),
        (5, 5),
        (5, 6), (6, 6), (7, 6), (8, 6), (9, 6),
    }
    return tuple(sorted(filled))


def required_size_42() -> tuple[int, int]:
    """Return the minimum (width, height) in cells required for the
    '42' pattern

    Returns:
        Tuple (min_width, min_height).
    """
    offsets = _bitmap_42()
    max_x = max(x for x, _ in offsets)
    max_y = max(y for _, y in offsets)
    # Add 2-cell margin on each side so the pattern is not flush against walls
    return max_x + 3, max_y + 3


def place_42_cells(
    width: int, height: int
) -> Optional[tuple[tuple[int, int], ...]]:
    """Compute absolute (x, y) positions for the '42' pattern
    centred in the maze.

    Args:
        width: Maze width in cells.
        height: Maze height in cells.

    Returns:
        Tuple of absolute (x, y) cell positions, or None if the maze is
          too small.
    """
    req_w, req_h = required_size_42()
    if width < req_w or height < req_h:
        return None

    offsets = _bitmap_42()
    pat_w = max(x for x, _ in offsets) + 1
    pat_h = max(y for _, y in offsets) + 1

    ox = (width - pat_w) // 2
    oy = (height - pat_h) // 2

    cells = tuple((ox + x, oy + y) for x, y in offsets)

    for x, y in cells:
        if not (0 <= x < width and 0 <= y < height):
            raise AssertionError(
                f"42 placement out of bounds at ({x},{y}) for {width}x{height}"
            )
    return cells


def apply_pattern(
    maze: list[list[int]], cells: Iterable[tuple[int, int]]
) -> None:
    """Set every cell in *cells* to FULL_CELL (all 4 walls closed).

    Also updates the shared walls on neighbouring cells so the maze
    remains internally coherent (no mismatched wall pairs).

    Args:
        maze: Maze grid to modify in-place.
        cells: Iterable of (x, y) coordinates to close.
    """
    h = len(maze)
    w = len(maze[0]) if h else 0
    cell_set = set(cells)

    for x, y in cell_set:
        maze[y][x] = FULL_CELL

    # Fix wall coherence on the border of the pattern:
    # For each pattern cell's non-pattern neighbour,
    # add the wall facing the pattern.
    for x, y in cell_set:
        # North neighbour
        if y > 0 and (x, y - 1) not in cell_set:
            maze[y - 1][x] |= 4   # add South wall to the north neighbour
        # East neighbour
        if x + 1 < w and (x + 1, y) not in cell_set:
            maze[y][x + 1] |= 8   # add West wall to the east neighbour
        # South neighbour
        if y + 1 < h and (x, y + 1) not in cell_set:
            maze[y + 1][x] |= 1   # add North wall to the south neighbour
        # West neighbour
        if x > 0 and (x - 1, y) not in cell_set:
            maze[y][x - 1] |= 2   # add East wall to the west neighbour
