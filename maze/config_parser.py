"""Configuration parser for A-Maze-ing."""
from __future__ import annotations

from typing import Any, Optional


def load_config(path: str) -> dict[str, Any]:
    """Parse a KEY=VALUE configuration file for the maze generator.

    Lines beginning with '#' are treated as comments and ignored.
    Each valid line must contain exactly one '=' separator.

    Args:
        path: Path to the plain-text configuration file.

    Returns:
        Dictionary with fully typed configuration values.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If a required key is missing or a value is malformed.
    """
    raw: dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            raw[key.strip()] = value.strip()

    # Validate required keys
    required_keys = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE"]
    for k in required_keys:
        if k not in raw:
            raise ValueError(f"Missing required config key: {k}")

    def _bool(val: str) -> bool:
        """Parse a boolean-like string value."""
        return val.strip().lower() in {"1", "true", "yes", "on"}

    def _optional_int(key: str) -> Optional[int]:
        """Return int value for key or None if absent."""
        return int(raw[key]) if key in raw else None

    def _parse_coord(val: str, key: str) -> tuple[int, int]:
        """Parse 'x,y' coordinate string into a tuple of ints."""
        parts = val.split(",")
        if len(parts) != 2:
            raise ValueError(
                f"Config key {key} must be in 'x,y' format, got: {val}")
        try:
            return (int(parts[0].strip()), int(parts[1].strip()))
        except ValueError:
            raise ValueError(f"Config key {key} contains non-integer: {val}")

    width = int(raw["WIDTH"])
    height = int(raw["HEIGHT"])

    if width < 1 or height < 1:
        raise ValueError("WIDTH and HEIGHT must be positive integers.")

    entry = _parse_coord(raw["ENTRY"], "ENTRY")
    exit_ = _parse_coord(raw["EXIT"], "EXIT")

    if not (0 <= entry[0] < width and 0 <= entry[1] < height):
        raise ValueError(
            f"ENTRY {entry} is out of maze bounds ({width}x{height})."
        )
    if not (0 <= exit_[0] < width and 0 <= exit_[1] < height):
        raise ValueError(
            f"EXIT {exit_} is out of maze bounds ({width}x{height})."
        )
    if entry == exit_:
        raise ValueError("ENTRY and EXIT must be different cells.")

    return {
        "WIDTH": width,
        "HEIGHT": height,
        "ENTRY": entry,
        "EXIT": exit_,
        "OUTPUT_FILE": raw["OUTPUT_FILE"],
        "ALGORITHM": raw.get("ALGORITHM", "wilson").lower(),
        "SEED": _optional_int("SEED"),
        "PERFECT": _bool(raw["PERFECT"]) if "PERFECT" in raw else False,
        "DRAW_42": _bool(raw["DRAW_42"]) if "DRAW_42" in raw else False,
        "COLOR_42": raw.get("COLOR_42"),
        "CUSTOM_IMAGE": raw.get("CUSTOM_IMAGE"),
        "CANVAS_BG": raw.get("CANVAS_BG", "#fff0f5"),
        "PATH_COLOR": raw.get("PATH_COLOR", "#e75480"),
    }
