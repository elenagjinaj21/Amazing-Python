"""Uniqueness / perfect-maze verification helpers."""
from __future__ import annotations

from collections import deque


def _open_neighbors(
    maze: list[list[int]], x: int, y: int
) -> list[tuple[int, int]]:
    """Return all cells reachable from (x, y) through carved passages.

    Args:
        maze: The maze grid.
        x: Column of the current cell.
        y: Row of the current cell.

    Returns:
        List of (nx, ny) cells that share an open wall with (x, y).
    """
    h = len(maze)
    w = len(maze[0])
    result: list[tuple[int, int]] = []
    # North
    if y > 0 and not (maze[y][x] & 1):
        result.append((x, y - 1))
    # East
    if x + 1 < w and not (maze[y][x] & 2):
        result.append((x + 1, y))
    # South
    if y + 1 < h and not (maze[y][x] & 4):
        result.append((x, y + 1))
    # West
    if x > 0 and not (maze[y][x] & 8):
        result.append((x - 1, y))
    return result


def entry_exit_has_unique_path(
    maze: list[list[int]],
    entry: tuple[int, int],
    exit_: tuple[int, int],
) -> bool:
    """Return True iff there is exactly one simple path from entry to exit.

    Uses the spanning-tree property: a connected acyclic graph on V vertices
    has exactly V-1 edges. We BFS the connected component of *entry* and
    count its edges; if edges == vertices - 1 and exit is reachable, the
    maze is a perfect tree.

    Args:
        maze: 2-D cell grid.
        entry: Starting (x, y) cell.
        exit_: Target (x, y) cell.

    Returns:
        True if the maze forms a spanning tree connecting entry and exit.
    """
    ex, ey = entry
    tx, ty = exit_
    h = len(maze)
    w = len(maze[0])

    start: tuple[int, int] = (ex, ey)
    q: deque[tuple[int, int]] = deque([start])
    seen: set[tuple[int, int]] = {start}

    while q:
        x, y = q.popleft()
        for nx, ny in _open_neighbors(maze, x, y):
            if (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny))

    if (tx, ty) not in seen:
        return False

    # Count undirected edges in the component
    edges = 0
    for x, y in seen:
        if x + 1 < w and (x + 1, y) in seen and not (maze[y][x] & 2):
            edges += 1
        if y + 1 < h and (x, y + 1) in seen and not (maze[y][x] & 4):
            edges += 1

    return edges == len(seen) - 1
