"""BFS solver – finds the shortest path through a maze."""
from __future__ import annotations

from collections import deque

# (dx, dy, wall_bitmask_blocking_move, direction_letter)
DIRS = [(0, -1, 1, "N"), (1, 0, 2, "E"), (0, 1, 4, "S"), (-1, 0, 8, "W")]


def solve_bfs(
    maze: list[list[int]],
    start: tuple[int, int],
    end: tuple[int, int],
) -> list[str]:
    """Find the shortest path from start to end using breadth-first search.

    Args:
        maze: 2-D list of cells with wall bitmasks (N=1, E=2, S=4, W=8).
        start: (x, y) starting cell.
        end: (x, y) target cell.

    Returns:
        List of direction letters (N/E/S/W) describing the shortest path,
        or an empty list if no path exists.
    """
    if start == end:
        return []

    queue: deque[tuple[tuple[int, int], list[str]]] = deque([(start, [])])
    visited: set[tuple[int, int]] = {start}

    while queue:
        (x, y), path = queue.popleft()
        if (x, y) == end:
            return path
        for dx, dy, wall, move in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= ny < len(maze) and 0 <= nx < len(maze[0]):
                if not (maze[y][x] & wall) and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [move]))
    return []
