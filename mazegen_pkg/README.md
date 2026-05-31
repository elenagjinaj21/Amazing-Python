# mazegen

A reusable Python maze generation library.

## Installation

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

## Usage

```python
from mazegen import MazeGenerator

# Basic maze
gen = MazeGenerator(width=20, height=15, seed=42)
maze = gen.generate()

# Solve it
path = gen.solve(start=(0, 0), end=(19, 14))
print("".join(path))

# Perfect maze with 42 pattern
gen = MazeGenerator(
    width=20, height=15, seed=42,
    algorithm="wilson",
    perfect=True,
    draw_42=True,
    entry=(0, 0),
    exit_=(19, 14),
)
maze = gen.generate()
```

## Cell encoding

Each cell is an integer 0–15 encoding which walls are **closed**:

| Bit | Value | Direction |
|-----|-------|-----------|
| 0   | 1     | North     |
| 1   | 2     | East      |
| 2   | 4     | South     |
| 3   | 8     | West      |
