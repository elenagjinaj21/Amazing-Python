"""mazegen – reusable maze generation library.

A standalone Python package for generating perfect and imperfect mazes,
with optional '42' pattern embedding and BFS path solving.

Quick-start::

    from mazegen import MazeGenerator

    # Basic usage
    gen = MazeGenerator(width=20, height=15, seed=42)
    maze = gen.generate()

    # maze is list[list[int]]; each int encodes walls as 4 bits:
    #   bit 0 (1) = North wall closed
    #   bit 1 (2) = East  wall closed
    #   bit 2 (4) = South wall closed
    #   bit 3 (8) = West  wall closed

    # Access cell walls
    cell = maze[row][col]
    has_north = bool(cell & 1)
    has_east  = bool(cell & 2)
    has_south = bool(cell & 4)
    has_west  = bool(cell & 8)

    # Solve the maze (BFS shortest path)
    path = gen.solve(start=(0, 0), end=(19, 14))
    # path is a list of 'N'/'E'/'S'/'W' letters

Custom parameters::

    gen = MazeGenerator(
        width=30,
        height=20,
        seed=999,
        algorithm="dfs",   # or "wilson" (default)
        perfect=True,      # exactly one path between entry and exit
        draw_42=True,      # embed the '42' glyph as fully-closed cells
        entry=(0, 0),
        exit_=(29, 19),
    )
    maze = gen.generate()
    path = gen.solve(start=(0, 0), end=(29, 19))
"""
from __future__ import annotations

import random
from collections import deque
from typing import Optional

__version__ = "1.0.0"
__all__ = ["MazeGenerator"]

# ── Wall bitmasks ───────────────────────────────────────────────────────
_N, _E, _S, _W = 1, 2, 4, 8
_DIRS = [(0, -1, _N, _S), (1, 0, _E, _W), (0, 1, _S, _N), (-1, 0, _W, _E)]
_FULL = 15  # all 4 walls closed


# ── Internal generation helpers ─────────────────────────────────────────

def _full_grid(w: int, h: int) -> list[list[int]]:
    """Return a grid where every cell has all walls closed."""
    return [[_FULL] * w for _ in range(h)]


def _carve(maze: list[list[int]], x1: int, y1: int,
           x2: int, y2: int, wall: int, opp: int) -> None:
    """Remove the shared wall between two adjacent cells."""
    maze[y1][x1] &= ~wall
    maze[y2][x2] &= ~opp


def _dfs(w: int, h: int, seed: Optional[int]) -> list[list[int]]:
    """Iterative depth-first search (recursive backtracker) maze generator."""
    rng = random.Random(seed)
    maze = _full_grid(w, h)
    stack = [(0, 0)]
    visited: set[tuple[int, int]] = {(0, 0)}
    while stack:
        x, y = stack[-1]
        nbrs = [
            (x + dx, y + dy, wl, op)
            for dx, dy, wl, op in _DIRS
            if 0 <= x + dx < w and 0 <= y + dy < h
            and (x + dx, y + dy) not in visited
        ]
        if nbrs:
            nx, ny, wl, op = rng.choice(nbrs)
            _carve(maze, x, y, nx, ny, wl, op)
            visited.add((nx, ny))
            stack.append((nx, ny))
        else:
            stack.pop()
    return maze


def _wilson(w: int, h: int, seed: Optional[int]) -> list[list[int]]:
    """Wilson's loop-erased random walk – produces uniform spanning trees."""
    rng = random.Random(seed)
    maze = _full_grid(w, h)
    unvisited: set[tuple[int, int]] = {(x, y)
                                       for x in range(w) for y in range(h)}
    unvisited.discard(rng.choice(list(unvisited)))
    while unvisited:
        cell = rng.choice(list(unvisited))
        path: list[tuple[int, int]] = [cell]
        while path[-1] in unvisited:
            x, y = path[-1]
            valid = [
                (x + dx, y + dy, wl, op)
                for dx, dy, wl, op in _DIRS
                if 0 <= x + dx < w and 0 <= y + dy < h
            ]
            nx, ny, _wl, _op = rng.choice(valid)
            if (nx, ny) in path:
                path = path[:path.index((nx, ny)) + 1]
            else:
                path.append((nx, ny))
        for i in range(len(path) - 1):
            x, y = path[i]
            nx, ny = path[i + 1]
            for dx, dy, wl, op in _DIRS:
                if x + dx == nx and y + dy == ny:
                    _carve(maze, x, y, nx, ny, wl, op)
                    break
            unvisited.discard((x, y))
        unvisited.discard(path[-1])
    return maze


def _bfs(maze: list[list[int]], start: tuple[int, int],
         end: tuple[int, int]) -> list[str]:
    """BFS shortest-path solver. Returns direction letters or empty list."""
    if start == end:
        return []
    h, w = len(maze), len(maze[0])
    q: deque[tuple[tuple[int, int], list[str]]] = deque([(start, [])])
    seen: set[tuple[int, int]] = {start}
    while q:
        (x, y), path = q.popleft()
        if (x, y) == end:
            return path
        for dx, dy, wl, mv in [(0, -1, _N, "N"), (1, 0, _E, "E"),
                               (0, 1, _S, "S"), (-1, 0, _W, "W")]:
            nx, ny = x + dx, y + dy
            if 0 <= ny < h and 0 <= nx < w and not (maze[y][x] & wl):
                if (nx, ny) not in seen:
                    seen.add((nx, ny))
                    q.append(((nx, ny), path + [mv]))
    return []


def _is_spanning_tree(maze: list[list[int]], entry: tuple[int, int],
                      exit_: tuple[int, int]) -> bool:
    """Return True if the maze component is a spanning tree (perfect maze)."""
    h, w = len(maze), len(maze[0])
    q: deque[tuple[int, int]] = deque([entry])
    seen: set[tuple[int, int]] = {entry}
    while q:
        x, y = q.popleft()
        for dx, dy, wl, _op in _DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not (maze[y][x] & wl):
                if (nx, ny) not in seen:
                    seen.add((nx, ny))
                    q.append((nx, ny))
    if exit_ not in seen:
        return False
    edges = sum(
        (1 if x + 1 < w and (x + 1, y) in seen
         and not (maze[y][x] & _E) else 0) +
        (1 if y + 1 < h and (x, y + 1) in seen
         and not (maze[y][x] & _S) else 0)
        for x, y in seen
    )
    return edges == len(seen) - 1


def _apply_42(
        maze: list[list[int]],
        cells: tuple[tuple[int, int], ...],
        w: int, h: int) -> None:
    """Close all pattern cells and fix neighbour wall coherence."""
    cell_set = set(cells)
    for x, y in cell_set:
        maze[y][x] = _FULL
    for x, y in cell_set:
        if y > 0 and (x, y - 1) not in cell_set:
            maze[y - 1][x] |= 4
        if x + 1 < w and (x + 1, y) not in cell_set:
            maze[y][x + 1] |= 8
        if y + 1 < h and (x, y + 1) not in cell_set:
            maze[y + 1][x] |= 1
        if x > 0 and (x - 1, y) not in cell_set:
            maze[y][x - 1] |= 2


def _place_42(w: int, h: int) -> Optional[tuple[tuple[int, int], ...]]:
    """Return centred (x,y) positions for '42', or None if too small."""
    offsets = (
        (0, 0), (3, 0), (0, 1), (3, 1), (0, 2), (3, 2),
        (0, 3), (1, 3), (2, 3), (3, 3), (3, 4), (3, 5), (3, 6),
        (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (9, 1), (9, 2),
        (5, 3), (6, 3), (7, 3), (8, 3), (9, 3), (5, 4), (5, 5),
        (5, 6), (6, 6), (7, 6), (8, 6), (9, 6),
    )
    req_w = max(x for x, _ in offsets) + 3
    req_h = max(y for _, y in offsets) + 3
    if w < req_w or h < req_h:
        return None
    pat_w = max(x for x, _ in offsets) + 1
    pat_h = max(y for _, y in offsets) + 1
    ox, oy = (w - pat_w) // 2, (h - pat_h) // 2
    return tuple((ox + x, oy + y) for x, y in offsets)


# ── Public class ────────────────────────────────────────────────────────

class MazeGenerator:
    """Generate configurable mazes and optionally solve them.

    Example::

        gen = MazeGenerator(width=20, height=15, seed=42)
        maze = gen.generate()
        path = gen.solve(start=(0, 0), end=(19, 14))
    """

    def __init__(
        self,
        width: int,
        height: int,
        seed: Optional[int] = None,
        algorithm: str = "wilson",
        perfect: bool = False,
        draw_42: bool = False,
        entry: Optional[tuple[int, int]] = None,
        exit_: Optional[tuple[int, int]] = None,
    ) -> None:
        """Initialise the generator.

        Args:
            width: Number of maze columns.
            height: Number of maze rows.
            seed: RNG seed for reproducibility (None = random each run).
            algorithm: 'dfs' or 'wilson' (default).
            perfect: Guarantee exactly one entry-to-exit path.
            draw_42: Embed '42' glyph as fully-closed cells.
            entry: (x, y) entry cell; required when perfect or draw_42.
            exit_: (x, y) exit cell; required when perfect or draw_42.
        """
        self.width = width
        self.height = height
        self.seed = seed
        self.algorithm = algorithm.lower()
        self.perfect = perfect
        self.draw_42 = draw_42
        self.entry = entry
        self.exit_ = exit_
        self._maze: Optional[list[list[int]]] = None

    def _once(self, seed: Optional[int]) -> list[list[int]]:
        fn = _dfs if self.algorithm == "dfs" else _wilson
        return fn(self.width, self.height, seed)

    def generate(self) -> list[list[int]]:
        """Generate the maze and cache it internally.

        Returns:
            2-D list of ints (0-15) encoding per-cell walls.
        """
        needs_coords = self.perfect or self.draw_42
        if needs_coords and (self.entry is None or self.exit_ is None):
            raise ValueError(
                "entry and exit_ required when perfect or draw_42 is set.")

        if not self.perfect and not self.draw_42:
            self._maze = self._once(self.seed)
            return self._maze

        if not self.perfect and self.draw_42:
            for attempt in range(200):
                seed_for_attempt = self.seed if attempt == 0 else (
                    self.seed + attempt if self.seed is not None else None
                )
                maze = self._once(seed_for_attempt)
                cells = _place_42(self.width, self.height)
                if cells is None:
                    self._maze = maze
                    return maze
                _apply_42(maze, cells, self.width, self.height)
                if (self.entry is not None and self.exit_ is not None
                        and _bfs(maze, self.entry, self.exit_)):
                    self._maze = maze
                    return maze
            self._maze = self._once(self.seed)
            return self._maze

        # Perfect mode — use incremental seeds so the same base seed always
        # produces the same result while still allowing retries.
        for attempt in range(200):
            s_perfect: Optional[int] = (
                None if self.seed is None else self.seed + attempt)
            maze = self._once(s_perfect)
            if self.draw_42:
                cells = _place_42(self.width, self.height)
                if cells:
                    _apply_42(maze, cells, self.width, self.height)
            if _is_spanning_tree(
                    maze, self.entry, self.exit_):  # type: ignore[arg-type]
                self._maze = maze
                return maze
        self._maze = self._once(self.seed)
        return self._maze

    def solve(
        self,
        start: Optional[tuple[int, int]] = None,
        end: Optional[tuple[int, int]] = None,
    ) -> list[str]:
        """Return BFS shortest path through generated maze.
        Args:
            start: (x, y) start cell (defaults to self.entry).
            end: (x, y) end cell (defaults to self.exit_).

        Returns:
            List of direction letters ('N', 'E', 'S', 'W').

        Raises:
            RuntimeError: If generate() has not been called yet.
        """
        if self._maze is None:
            raise RuntimeError("Call generate() before solve().")
        s = start or self.entry or (0, 0)
        e = end or self.exit_ or (self.width - 1, self.height - 1)
        return _bfs(self._maze, s, e)
