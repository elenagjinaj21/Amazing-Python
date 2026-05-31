"""Entry point for A-Maze-ing maze generator.

Usage
-----
    python3 a_maze_ing.py config.txt              # interactive mode selection
    python3 a_maze_ing.py config.txt --gui        # launch Pygame GUI directly
    python3 a_maze_ing.py config.txt --ascii      # launch ASCII terminal mode
"""
from __future__ import annotations

import sys

from maze.config_parser import load_config
from maze.generator import MazeGenerator
from maze.solver import solve_bfs
from maze.writer import write_output


def _choose_mode() -> str:
    """Prompt the user to select a display mode.

    Returns:
        'gui' or 'ascii'.
    """
    print()
    print("  ♥  A-Maze-ing  ♥")
    print()
    print("  Select display mode:")
    print("    [1] Pygame GUI    graphical window with pink theme")
    print("    [2] ASCII         Unicode terminal rendering")
    print()
    while True:
        try:
            choice = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit(0)
        if choice in ("1", "gui", "pygame"):
            return "gui"
        if choice in ("2", "ascii", "terminal"):
            return "ascii"
        print("  Please enter 1 or 2.")


def main() -> None:
    """Parse config, generate maze, write output file, and launch display.

    Raises:
        SystemExit: On invalid arguments or configuration errors.
    """
    # ── Argument parsing ────────────────────────────────────────────────────
    args = sys.argv[1:]
    mode_flag: str | None = None

    filtered: list[str] = []
    for arg in args:
        if arg in ("--gui", "-g"):
            mode_flag = "gui"
        elif arg in ("--ascii", "-a"):
            mode_flag = "ascii"
        else:
            filtered.append(arg)

    if len(filtered) != 1:
        print("Usage: python3 a_maze_ing.py config.txt [--gui | --ascii]")
        raise SystemExit(1)

    config_path = filtered[0]

    # ── Config ──────────────────────────────────────────────────────────────
    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        print(f"Error: config file not found: {exc}")
        raise SystemExit(1)
    except (KeyError, ValueError) as exc:
        print(f"Error: invalid config: {exc}")
        raise SystemExit(1)

    # ── Maze generation ─────────────────────────────────────────────────────
    try:
        generator = MazeGenerator(
            width=config["WIDTH"],
            height=config["HEIGHT"],
            seed=config["SEED"],
            algorithm=config["ALGORITHM"],
            perfect=config["PERFECT"],
            draw_42=config["DRAW_42"],
            entry=config["ENTRY"],
            exit_=config["EXIT"],
        )
        maze = generator.generate()
    except Exception as exc:
        print(f"Error generating maze: {exc}")
        raise SystemExit(1)

    path = solve_bfs(maze, config["ENTRY"], config["EXIT"])

    try:
        write_output(maze, config["OUTPUT_FILE"], config["ENTRY"],
                     config["EXIT"], path)
    except OSError as exc:
        print(f"Warning: could not write output file: {exc}")

    # ── Mode selection ──────────────────────────────────────────────────────
    mode = mode_flag or _choose_mode()

    if mode == "ascii":
        from maze.ascii_renderer import MazeASCII
        app: MazeASCII = MazeASCII(
            maze=maze,
            entry=config["ENTRY"],
            exit_=config["EXIT"],
            path=path,
            config=config,
        )
        app.run()
    else:
        from maze.gui import MazeGUI
        gui = MazeGUI(
            maze=maze,
            entry=config["ENTRY"],
            exit_=config["EXIT"],
            path=path,
            config=config,
        )
        gui.run()


if __name__ == "__main__":
    main()
