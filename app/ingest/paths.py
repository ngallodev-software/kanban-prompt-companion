from __future__ import annotations

from pathlib import Path


_EXCLUDED_SUFFIXES = (".swp", ".swx", ".tmp", ".part", ".crdownload")


def is_processable_markdown_path(path: str | Path) -> bool:
    candidate = Path(path)
    if candidate.is_dir():
        return False
    if candidate.suffix.lower() != ".md":
        return False

    lower_name = candidate.name.lower()
    if lower_name.startswith(("~", "._", ".")) or lower_name.endswith(("~", ".tmp")):
        return False
    if any(lower_name.endswith(suffix) for suffix in _EXCLUDED_SUFFIXES):
        return False

    for part in candidate.parts:
        if part.startswith("."):
            return False

    return True
