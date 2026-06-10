*This activity has been created as part of the 42 curriculum by egjinaj & shajdar.*

# A-Maze-ing

## Description

**A-Maze-ing** is a Python maze generator and interactive visualiser built as part of the 42 curriculum. Given a configuration file, the program generates a maze (optionally perfect — with exactly one path between entry and exit), optionally embeds a visible **"42"** pattern, writes the result to a hex-encoded output file, and lets you explore it in one of two display modes:

- **Pygame GUI** — a pink-themed graphical window where you can toggle the solution path, change colours, cycle the corner image, and regenerate new mazes.
- **ASCII terminal** — a Unicode box-drawing rendering of the same maze printed directly in your terminal, with the same regenerate and path-toggle controls available via keyboard input.

Both modes share identical maze generation and solving logic; only the rendering layer differs.

---

## Instructions

### Requirements

- Python 3.10 or later
- `pygame` — install with `pip install pygame`
- No other third-party packages are required

### Installation

```bash
pip install pygame

# Optional: install lint tools
make install
```

### Running

```bash
# Interactive mode selection prompt (choose GUI or ASCII at startup)
python3 a_maze_ing.py config.txt

# Launch the Pygame GUI directly
python3 a_maze_ing.py config.txt --gui

# Launch ASCII terminal mode directly
python3 a_maze_ing.py config.txt --ascii
```

When run without a flag, the program prints a short menu:

```
  [1] Pygame GUI   – graphical window with pink theme
  [2] ASCII        – Unicode terminal rendering
```

### Lint / type-check

```bash
make lint
make lint-strict   # optional stricter mypy
```

### Debug mode

```bash
make debug
```

### Clean build artefacts

```bash
make clean
```

---

## Configuration File Format

The config file uses one `KEY=VALUE` pair per line. Lines beginning with `#` are comments and are ignored.

| Key            | Required | Description                                    | Example                        |
|----------------|----------|------------------------------------------------|--------------------------------|
| `WIDTH`        | ✓        | Maze width in cells                            | `WIDTH=20`                     |
| `HEIGHT`       | ✓        | Maze height in cells                           | `HEIGHT=15`                    |
| `ENTRY`        | ✓        | Entry cell coordinates `x,y`                   | `ENTRY=0,0`                    |
| `EXIT`         | ✓        | Exit cell coordinates `x,y`                    | `EXIT=19,14`                   |
| `OUTPUT_FILE`  | ✓        | Output filename for the hex-encoded maze       | `OUTPUT_FILE=maze.txt`         |
| `PERFECT`      |          | `True` = exactly one entry↔exit path           | `PERFECT=True`                 |
| `ALGORITHM`    |          | `wilson` (default) or `dfs`                    | `ALGORITHM=wilson`             |
| `SEED`         |          | Integer RNG seed for reproducibility           | `SEED=42`                      |
| `DRAW_42`      |          | Embed the '42' pattern as fully-closed cells   | `DRAW_42=true`                 |
| `CUSTOM_IMAGE` |          | Path to a PNG image shown in the GUI corner    | `CUSTOM_IMAGE=hellokitty.png`  |
| `COLOR_42`     |          | Hex colour for the '42' pattern cells          | `COLOR_42=#f06292`             |
| `PATH_COLOR`   |          | Hex colour for the solution path overlay       | `PATH_COLOR=#e91e63`           |
| `CANVAS_BG`    |          | Hex colour for the maze floor background       | `CANVAS_BG=#fff0f5`            |

**Minimal example `config.txt`:**

```
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
ALGORITHM=wilson
PERFECT=True
DRAW_42=true
```

---

## Output File Format

The output file contains one uppercase hex digit per cell (wall bitmask), one row per line, followed by an empty line, then the entry coordinates, exit coordinates, and the shortest path as a string of `N`/`E`/`S`/`W` letters.

**Wall bitmask encoding:**

| Bit | Value | Direction |
|-----|-------|-----------|
| 0   | 1     | North     |
| 1   | 2     | East      |
| 2   | 4     | South     |
| 3   | 8     | West      |

A closed wall sets the bit to `1`; open means `0`.

**Example output:**

```
9515391539551795151151153
EBABAE812853C1412BA812812
...

0,0
19,14
SSSSEESSESEESSEE...
```

---

## Maze Generation Algorithms

This project implements two algorithms, selectable via the `ALGORITHM` config key.

### Wilson's algorithm (default: `ALGORITHM=wilson`)

Wilson's algorithm performs a **loop-erased random walk**. It picks a random unvisited cell, walks randomly until it hits a visited cell — erasing any loop that forms — then carves the resulting path into the maze. This repeats until every cell is visited.

**Why Wilson's?** It produces **uniformly random spanning trees**: every possible perfect maze layout is equally likely. The result has no directional bias, no long-corridor texture, and is visually balanced and harder to solve by intuition.

### DFS — depth-first search (`ALGORITHM=dfs`)

The iterative backtracker starts at a cell, carves into an unvisited neighbour chosen at random, and backtracks when no unvisited neighbours remain. It is significantly faster than Wilson's on large mazes but introduces a directional bias that produces long winding corridors and a recognisable texture.

---

## Advanced Features

### Dual display modes

The rendering layer is fully separated from the maze logic. After generation, the user (or a `--gui` / `--ascii` flag) selects one of two independent renderers:

- **Pygame GUI** (`maze/gui.py`) — fixed 1800×1100 window, pink colour palette, in-window HSV colour picker, corner image with four cycling positions, keyboard shortcuts mirroring every button.
- **ASCII terminal** (`maze/ascii_renderer.py`) — Unicode box-drawing characters (`┌`, `┬`, `┼`, …), ANSI colour highlighting for walls, path, entry/exit, and the 42 pattern, interactive prompt with the same regenerate and path-toggle actions.

Both renderers receive the identical `maze`, `entry`, `exit_`, `path`, and `config` objects produced by the shared generation pipeline. No maze logic is duplicated.

### Perfect-maze enforcement

When `PERFECT=True`, the generator retries up to 200 times (using incremental seeds for reproducibility) until the maze forms a spanning tree — verified by checking that the number of edges in the connected component equals the number of vertices minus one.

### '42' pattern embedding

When `DRAW_42=True`, a bitmap glyph of the digits "42" is centred in the maze by closing all walls of the relevant cells. Neighbour wall coherence is repaired automatically. The generator retries if the pattern blocks the only entry-to-exit path.

---

## Reusable Code

The `MazeGenerator` class in `maze/generator.py` is the reusable core of this project. It is also packaged as a standalone pip-installable wheel (`mazegen-1.0.0-py3-none-any.whl`) at the root of the repository.

### Install the package

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

### Usage

```python
from mazegen import MazeGenerator

# Basic maze
gen = MazeGenerator(width=20, height=15, seed=42)
maze = gen.generate()

# maze is list[list[int]]: each int encodes walls as a 4-bit bitmask
cell = maze[row][col]
has_north = bool(cell & 1)
has_east  = bool(cell & 2)
has_south = bool(cell & 4)
has_west  = bool(cell & 8)

# Solve (BFS shortest path)
path = gen.solve(start=(0, 0), end=(19, 14))
print("".join(path))  # e.g. "SSSEEESSSE..."

# Perfect maze with 42 pattern
gen = MazeGenerator(
    width=20, height=15, seed=42,
    algorithm="dfs",     # or "wilson" (default)
    perfect=True,
    draw_42=True,
    entry=(0, 0),
    exit_=(19, 14),
)
maze = gen.generate()
```

### Rebuild the package

```bash
cd mazegen_pkg
pip install build
python3 -m build --wheel
```

---

## Display Interactions

### Pygame GUI

| Key / Button       | Effect                                              |
|--------------------|-----------------------------------------------------|
| `1` / Regenerate   | Generate a new random maze with a fresh seed        |
| `2` / Toggle Path  | Show or hide the BFS solution path overlay          |
| `3` / Wall Color   | Open the HSV colour picker to change wall colour    |
| `4` / 42 Color     | Open the colour picker for the '42' pattern cells   |
| `5` / BG Color     | Open the colour picker for the maze background      |
| `6` / Find Kitty   | Cycle the corner image through four positions       |
| `7` / Quit         | Close the application                               |
| `Esc`              | Close the application                               |

### ASCII terminal

| Input | Effect                                  |
|-------|-----------------------------------------|
| `1`   | Regenerate with a new random seed       |
| `2`   | Toggle the solution path on / off       |
| `q`   | Quit                                    |

---

## Team & Project Management

### Team members

- `egjinaj` — Maze generation algorithms (`algorithms.py`, `generator.py`), perfect-maze verification logic (`perfect.py`, `constraints.py`), BFS solver (`solver.py`), reusable `mazegen` package.
- `shajdar` — Pygame GUI (`gui.py`), output file format (`writer.py`), config parser (`config_parser.py`), '42' pattern placement (`pattern.py`), ASCII renderer (`ascii_renderer.py`), entry point and mode-selection logic (`a_maze_ing.py`).

### Planning

Initial estimate: 4 days for core generation + GUI. Actual timeline stretched by roughly one extra day:

- Day 1–2: Wilson's and DFS algorithms, BFS solver, config parser, output writer.
- Day 3: Pygame GUI, colour picker, image corner feature.
- Day 4: Perfect-maze retry logic and '42' pattern — both took longer than expected because pattern insertion can break the unique-path constraint, requiring iterative regeneration.
- Day 5 (unplanned): ASCII renderer and dual-mode entry point, README finalisation.

### What worked well

- Wilson's algorithm was clean to implement and produced visually appealing, unbiased mazes from the start.
- Separating the maze data model (bitmask grid) from all rendering code made adding the ASCII mode straightforward — the renderer only reads the existing grid, no logic changes needed.
- Incremental seeding for the perfect-maze retry loop ensures that the same base `SEED` always produces the same result while still allowing variation across retries.

### What could be improved

- The '42' pattern retry loop can be slow for small mazes with `PERFECT=True`; a smarter placement strategy that avoids blocking the critical path would remove the need for retries.
- A proper test suite with `pytest` would increase confidence in edge cases (minimum maze size, pattern placement bounds, solver correctness).
- The Pygame window size is hardcoded; a resizable layout would improve usability on smaller screens.

### Tools used

- VS Code with the Python and mypy extensions
- `mypy` and `flake8` for static analysis and linting
- Claude (Anthropic) as an AI assistant — see AI usage section below

---

## Resources

- [Wilson's algorithm (Wikipedia)](https://en.wikipedia.org/wiki/Maze_generation_algorithm#Wilson's_algorithm)
- [Maze generation algorithms overview](https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap.html)
- [Python `random` module documentation](https://docs.python.org/3/library/random.html)
- [BFS shortest path (Wikipedia)](https://en.wikipedia.org/wiki/Breadth-first_search)
- [pygame documentation](https://www.pygame.org/docs/)
- [Unicode box-drawing characters](https://en.wikipedia.org/wiki/Box-drawing_characters)

### AI usage

Claude (Anthropic) was used throughout this project for the following tasks:

- Suggesting the Wilson's algorithm implementation structure and the loop-erasure step.
- Adding the dual-mode entry point (`--gui` / `--ascii` flags and the interactive menu) and confirming that no maze logic needed to be duplicated.

All AI-generated content was reviewed, understood, manually tested, and modified before inclusion. No code was submitted without being read and verified by a team member.
