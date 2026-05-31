"""MazeGenerator – reusable maze generation class.

This module exposes a single ``MazeGenerator`` class that can be imported
into any Python project and installed via pip as the ``mazegen`` package.

Quick-start example::

    from maze.generator import MazeGenerator

    gen = MazeGenerator(width=20, height=15, seed=42)
    maze = gen.generate()
    # maze is a list[list[int]]: each int encodes walls as a 4-bit bitmask
    # N=1 (bit 0), E=2 (bit 1), S=4 (bit 2), W=8 (bit 3)
    # A closed wall sets the bit to 1; open means 0.

Custom parameters example::

    gen = MazeGenerator(
        width=30,
        height=20,
        seed=123,           # reproducible output
        algorithm="dfs",    # "dfs" or "wilson" (default)
        perfect=True,       # exactly one path between entry and exit
        draw_42=True,       # embed the "42" pattern using fully-closed cells
        entry=(0, 0),
        exit_=(29, 19),
    )
    maze = gen.generate()

Accessing the solution::

    from maze.solver import solve_bfs

    path = solve_bfs(maze, start=(0, 0), end=(29, 19))
    # path is a list of direction letters, e.g. ['S', 'E', 'E', 'S', ...]

Accessing cell walls::

    cell = maze[row][col]           # integer 0-15
    has_north_wall = bool(cell & 1)
    has_east_wall  = bool(cell & 2)
    has_south_wall = bool(cell & 4)
    has_west_wall  = bool(cell & 8)
"""
from __future__ import annotations

from typing import Callable, Optional

from maze.algorithms import dfs_generate, wilson_generate
from maze.constraints import enforce_perfect_constraints, try_embed_42
from maze.solver import solve_bfs


class MazeGenerator:
    """Generate mazes with configurable algorithms and optional constraints.

    The generator can produce either DFS (recursive backtracker) or Wilson's
    loop-erased random walk mazes. When ``perfect=True`` the generator
    guarantees exactly one path between entry and exit. When ``draw_42=True``
    it embeds a visible '42' pattern made of fully-closed cells.

    Attributes:
        width: Number of maze columns.
        height: Number of maze rows.
        seed: RNG seed (None for random each run).
        algorithm: Generation algorithm name ('dfs' or 'wilson').
        perfect: Whether to enforce the perfect-maze constraint.
        draw_42: Whether to embed the '42' pixel pattern.
        entry: (x, y) entry cell.
        exit_: (x, y) exit cell.
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
        """Initialise the maze generator.

        Args:
            width: Number of columns (cells).
            height: Number of rows (cells).
            seed: Optional RNG seed for reproducibility.
            algorithm: 'dfs' for depth-first search or 'wilson' (default).
            perfect: If True, guarantee exactly one entry-to-exit path.
            draw_42: If True, embed the '42' glyph as fully-closed cells.
            entry: (x, y) entry cell; required when perfect or draw_42 is True.
            exit_: (x, y) exit cell; required when perfect or draw_42 is True.

        Raises:
            ValueError: If entry/exit are missing when required.
        """
        self.width = width
        self.height = height
        self.seed = seed
        self.algorithm = algorithm.lower()
        self.perfect = perfect
        self.draw_42 = draw_42
        self.entry = entry
        self.exit_ = exit_

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_once(self, seed: Optional[int] = None) -> list[list[int]]:
        """Run the chosen algorithm once with the given seed.

        Args:
            seed: RNG seed for this single run.

        Returns:
            A freshly generated maze grid.
        """
        if self.algorithm == "dfs":
            return dfs_generate(self.width, self.height, seed)
        return wilson_generate(self.width, self.height, seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> list[list[int]]:
        """Generate and return the maze grid.

        The returned structure is a ``list[list[int]]`` where each integer
        encodes which walls of a cell are closed:

        * bit 0 (value 1) → North wall closed
        * bit 1 (value 2) → East wall closed
        * bit 2 (value 4) → South wall closed
        * bit 3 (value 8) → West wall closed

        Returns:
            2-D list of integers (0-15) representing the maze.

        Raises:
            ValueError: If entry/exit are missing when perfect or draw_42
                        is True.
        """
        needs_coords = self.perfect or self.draw_42
        if needs_coords and (self.entry is None or self.exit_ is None):
            msg = (
                "entry and exit_ must be provided when "
                "perfect=True or draw_42=True.")
            raise ValueError(msg)

        # ── Simple case: no perfect constraint, no '42' pattern ──────────────
        if not self.perfect and not self.draw_42:
            return self._make_once(self.seed)

        # ── Has draw_42 but no perfect requirement ───────────────────────────
        if not self.perfect and self.draw_42:
            assert self.entry is not None
            assert self.exit_ is not None
            last: Optional[list[list[int]]] = None
            for attempt in range(200):
                local_seed: Optional[int] = (self.seed if attempt == 0 else (
                    self.seed + attempt if self.seed is not None else None))
                maze = self._make_once(local_seed)
                embedded = try_embed_42(maze, self.width, self.height)
                if not embedded:
                    # Pattern does not fit – just return the plain maze
                    return maze
                if solve_bfs(maze, self.entry, self.exit_):
                    return maze
                last = maze
            return last or self._make_once(self.seed)

        # ── Perfect maze (with or without '42') ──────────────────────────────
        assert self.entry is not None
        assert self.exit_ is not None

        alg = self.algorithm

        # Use an incremental seed so the same base seed always produces
        # the same perfect maze, while still allowing retries.
        attempt_counter = [0]

        def make_maze() -> list[list[int]]:
            """Return a fresh maze with incrementing seed."""
            local_seed: Optional[int] = (
                None if self.seed is None
                else self.seed + attempt_counter[0]
            )
            attempt_counter[0] += 1
            if alg == "dfs":
                return dfs_generate(self.width, self.height, local_seed)
            return wilson_generate(self.width, self.height, local_seed)

        maker: Callable[[], list[list[int]]] = make_maze
        return enforce_perfect_constraints(
            generator_callable=maker,
            width=self.width,
            height=self.height,
            entry=self.entry,
            exit_=self.exit_,
            draw_42=self.draw_42,
        )
