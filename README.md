# A-Maze-ing

A-Maze-ing is a Python maze generation and visualization project with two display modes:
- a pink-themed **Pygame GUI**, and
- an **ASCII terminal renderer**.

It supports configurable maze dimensions, perfect maze enforcement, reproducible random seeds, and an optional embedded **42 pattern**.

---

## Features

- Generate mazes using **Wilson's algorithm** or **depth-first search (DFS)**
- Optional **perfect maze** generation with a single path between entry and exit
- Optional **42 pattern** embedding in the maze grid
- Dual visualization modes: **Pygame GUI** and **ASCII terminal**
- Hex-encoded maze output file with entry/exit coordinates and shortest path
- Reusable library core via `maze/generator.py`

---

## Requirements

- Python 3.10 or later
- `pygame` for GUI mode

---

## Installation

From the project root:

```bash
py -m pip install pygame
```

To install the package locally:

```bash
py -m pip install .
```

To install from the provided wheel:

```bash
py -m pip install mazegen-1.0.0-py3-none-any.whl
```

---

## Usage

Run the main script with a config file:

```bash
py a_maze_ing.py config.txt
```

Launch the GUI directly:

```bash
py a_maze_ing.py config.txt --gui
```

Launch ASCII mode directly:

```bash
py a_maze_ing.py config.txt --ascii
```

When no mode flag is provided, the program prompts for mode selection.

---

## Configuration

The configuration file uses one `KEY=VALUE` entry per line. Lines starting with `#` are ignored.

| Key            | Required | Description                                    | Example                        |
|----------------|----------|------------------------------------------------|--------------------------------|
| `WIDTH`        | ✓        | Maze width in cells                            | `WIDTH=20`                     |
| `HEIGHT`       | ✓        | Maze height in cells                           | `HEIGHT=15`                    |
| `ENTRY`        | ✓        | Entry cell coordinates `x,y`                   | `ENTRY=0,0`                    |
| `EXIT`         | ✓        | Exit cell coordinates `x,y`                   | `EXIT=19,14`                   |
| `OUTPUT_FILE`  | ✓        | Output filename for the hex-encoded maze       | `OUTPUT_FILE=maze.txt`         |
| `PERFECT`      |          | `True` = exactly one entry↔exit path           | `PERFECT=True`                 |
| `ALGORITHM`    |          | `wilson` (default) or `dfs`                    | `ALGORITHM=wilson`             |
| `SEED`         |          | Integer RNG seed for reproducibility           | `SEED=42`                      |
| `DRAW_42`      |          | Embed the `42` pattern into the maze cells     | `DRAW_42=true`                 |
| `CUSTOM_IMAGE` |          | Path to a PNG image shown in the GUI corner    | `CUSTOM_IMAGE=hellokitty.png`  |
| `COLOR_42`     |          | Hex colour for the `42` pattern cells          | `COLOR_42=#f06292`             |
| `PATH_COLOR`   |          | Hex colour for the solution path overlay       | `PATH_COLOR=#e91e63`           |
| `CANVAS_BG`    |          | Hex colour for the maze background             | `CANVAS_BG=#fff0f5`            |

**Example `config.txt`:**

```txt
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

## Output format

The output file contains:
1. A grid of uppercase hex digits representing wall bitmasks
2. A blank line
3. Entry coordinates
4. Exit coordinates
5. The shortest path as a sequence of `N`, `E`, `S`, `W`

Wall bitmask encoding:

| Bit | Value | Direction |
|-----|-------|-----------|
| 0   | 1     | North     |
| 1   | 2     | East      |
| 2   | 4     | South     |
| 3   | 8     | West      |

A closed wall sets the bit to `1`; an open path sets it to `0`.

---

## Project structure

- `a_maze_ing.py` — program entry point
- `config.txt` — sample configuration file
- `maze/` — package source code
- `mazegen_pkg/` — installable package metadata and package stub
- `maze.txt` — generated maze output example

Key source modules:
- `maze/generator.py` — maze generation core
- `maze/solver.py` — BFS path solver
- `maze/gui.py` — Pygame GUI renderer
- `maze/ascii_renderer.py` — terminal renderer
- `maze/writer.py` — hex output writer

---

## Python package usage

```python
from mazegen import MazeGenerator

generator = MazeGenerator(width=20, height=15, seed=42)
maze = generator.generate()
```

The returned maze is a list of rows containing 4-bit wall bitmasks.

---

## Development

Use `make` targets if available:

```bash
make lint
make lint-strict
make debug
make clean
```

---

## License

This project is licensed under the MIT License.

---
## Author
Project by Elena Gjinaj — https://github.com/elenagjinaj21
