from __future__ import annotations

import shutil
from pathlib import Path


def move_note_to_folder(
    note_path: str | Path,
    *,
    vault_path: str | Path,
    source_folder: str,
    target_folder: str,
) -> Path:
    source = Path(note_path)
    vault_root = Path(vault_path)
    source_root = vault_root / source_folder.strip().strip("/")
    target_root = vault_root / target_folder.strip().strip("/")

    if _is_within_root(source, target_root):
        return source

    relative_path = _relative_to_root(source, source_root)
    destination = target_root / relative_path
    if source == destination:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination = _unique_path(destination)
    shutil.move(str(source), str(destination))
    return destination


def _relative_to_root(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return Path(path.name)


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
