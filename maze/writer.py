"""Output file writer - saves maze data in the required hexadecimal format."""
from __future__ import annotations


def write_output(
    maze: list[list[int]],
    filename: str,
    entry: tuple[int, int],
    exit_: tuple[int, int],
    path: list[str],
) -> None:
    """Write maze data to a file using the hexadecimal wall-encoding format.

    Format:
        - One row per line, each cell encoded as an uppercase hex digit.
        - An empty line separator.
        - Entry coordinates as 'x,y'.
        - Exit coordinates as 'x,y'.
        - Shortest path as a string of N/E/S/W direction letters.
        - Every line ends with a newline character.

    Args:
        maze: 2-D list of cells (each int is a 0-15 wall bitmask).
        filename: Destination file path.
        entry: (x, y) entry cell coordinates.
        exit_: (x, y) exit cell coordinates.
        path: Solution path as a list of direction letters (N/E/S/W).

    Raises:
        OSError: If the file cannot be written.
    """
    with open(filename, "w", encoding="utf-8") as fh:
        for row in maze:
            fh.write("".join(format(cell, "X") for cell in row) + "\n")
        fh.write("\n")
        fh.write(f"{entry[0]},{entry[1]}\n")
        fh.write(f"{exit_[0]},{exit_[1]}\n")
        fh.write("".join(path) + "\n")
