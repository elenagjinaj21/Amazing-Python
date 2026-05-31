"""Maze generation algorithms: DFS and Wilson's loop-erased random walk."""
from __future__ import annotations

import random

# Wall bitmasks: bit 0 = North, bit 1 = East, bit 2 = South, bit 3 = West
N, E, S, W = 1, 2, 4, 8

# (dx, dy, wall_from_current, opposite_wall_in_neighbor)
DIRS = [(0, -1, N, S), (1, 0, E, W), (0, 1, S, N), (-1, 0, W, E)]


def _full_maze(width: int, height: int) -> list[list[int]]:
    """Return a grid where every cell has all 4 walls closed (bitmask 15).

    Args:
        width: Number of columns.
        height: Number of rows.

    Returns:
        2-D list of integers, all set to 15.
    """
    return [[15 for _ in range(width)] for _ in range(height)]


def _carve(
    maze: list[list[int]],
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    wall: int,
    opposite: int,
) -> None:
    """Remove the shared wall between two adjacent cells.

    Args:
        maze: The maze grid to modify in-place.
        x1: Column of the source cell.
        y1: Row of the source cell.
        x2: Column of the target cell.
        y2: Row of the target cell.
        wall: Bitmask of the wall to remove from the source cell.
        opposite: Bitmask of the corresponding wall to remove from target.
    """
    maze[y1][x1] &= ~wall
    maze[y2][x2] &= ~opposite


def dfs_generate(
    width: int, height: int, seed: int | None = None
) -> list[list[int]]:
    """Generate a perfect maze using iterative depth-first search.

    Produces a spanning-tree maze: every cell is reachable and there is
    exactly one path between any two cells.

    Args:
        width: Number of columns.
        height: Number of rows.
        seed: Optional RNG seed for reproducibility.

    Returns:
        2-D list of cells; each int encodes closed walls as a bitmask.
    """
    rng = random.Random(seed)
    maze = _full_maze(width, height)
    stack = [(0, 0)]
    visited: set[tuple[int, int]] = {(0, 0)}

    while stack:
        x, y = stack[-1]
        neighbors = []
        for dx, dy, wall, opp in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and (
                    nx, ny) not in visited:
                neighbors.append((nx, ny, wall, opp))
        if neighbors:
            nx, ny, wall, opp = rng.choice(neighbors)
            _carve(maze, x, y, nx, ny, wall, opp)
            visited.add((nx, ny))
            stack.append((nx, ny))
        else:
            stack.pop()
    return maze


def wilson_generate(
    width: int, height: int, seed: int | None = None
) -> list[list[int]]:
    """Generate uniform spanning tree maze via Wilson's algorithm.

    Produces an unbiased perfect maze where every spanning tree is equally
    likely. Slower than DFS for large mazes but statistically uniform.

    Args:
        width: Number of columns.
        height: Number of rows.
        seed: Optional RNG seed for reproducibility.

    Returns:
        2-D list of cells; each int encodes closed walls as a bitmask.
    """
    rng = random.Random(seed)
    maze = _full_maze(width, height)
    unvisited: set[tuple[int, int]] = {
        (x, y) for x in range(width) for y in range(height)
    }
    first = rng.choice(list(unvisited))
    unvisited.remove(first)

    while unvisited:
        cell = rng.choice(list(unvisited))
        path: list[tuple[int, int]] = [cell]

        while path[-1] in unvisited:
            x, y = path[-1]
            valid = []
            for dx, dy, wall, opp in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    valid.append((nx, ny, wall, opp))
            nx, ny, _w, _o = rng.choice(valid)
            nxt = (nx, ny)
            if nxt in path:
                # Erase the loop
                path = path[: path.index(nxt) + 1]
            else:
                path.append(nxt)

        # Carve the loop-erased path into the maze
        for i in range(len(path) - 1):
            x, y = path[i]
            nx, ny = path[i + 1]
            for dx, dy, wall, opp in DIRS:
                if x + dx == nx and y + dy == ny:
                    _carve(maze, x, y, nx, ny, wall, opp)
                    break
            unvisited.discard((x, y))
        unvisited.discard(path[-1])
    return maze
