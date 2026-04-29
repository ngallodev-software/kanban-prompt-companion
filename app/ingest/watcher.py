from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Callable

from watchdog.events import FileSystemEventHandler, FileSystemMovedEvent
from watchdog.observers import Observer

from app.ingest.dedupe import ContentHashCache
from app.ingest.markdown import load_note
from app.ingest.paths import is_processable_markdown_path
from app.ingest.stable_read import read_stable_text


@dataclass
class WatcherState:
    pending: dict[Path, float] = field(default_factory=dict)
    hash_cache: ContentHashCache = field(default_factory=ContentHashCache)
    lock: Lock = field(default_factory=Lock)


class NoteWatcher:
    def __init__(
        self,
        *,
        vault_path: str | Path,
        watch_folder: str,
        stabilization_seconds: float = 0.5,
        poll_interval_seconds: float = 0.1,
    ) -> None:
        self.vault_path = Path(vault_path)
        self.watch_folder = watch_folder.strip().strip("/")
        self.stabilization_seconds = stabilization_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.state = WatcherState()

    @property
    def watch_root(self) -> Path:
        return self.vault_path / self.watch_folder

    def startup_scan(self) -> list[Path]:
        root = self.watch_root
        if not root.exists():
            return []
        return sorted(
            path
            for path in root.rglob("*.md")
            if is_processable_markdown_path(path) and self._is_within_watch_root(path)
        )

    def enqueue(self, path: str | Path) -> None:
        candidate = Path(path)
        with self.state.lock:
            self.state.pending[candidate] = time.monotonic() + self.stabilization_seconds

    def drain_ready(self, now: float | None = None) -> list[Path]:
        now = time.monotonic() if now is None else now
        ready: list[Path] = []
        with self.state.lock:
            for path, deadline in list(self.state.pending.items()):
                if deadline <= now:
                    ready.append(path)
                    self.state.pending.pop(path, None)
        return ready

    def process_path(self, path: str | Path) -> object | None:
        candidate = Path(path)
        if not candidate.exists() or not is_processable_markdown_path(candidate):
            return None
        if not self._is_within_watch_root(candidate):
            return None

        raw_text = read_stable_text(
            candidate,
            timeout_seconds=max(2.0, self.stabilization_seconds * 4),
            poll_interval_seconds=self.poll_interval_seconds,
        )
        relative_path = self._relative_path(candidate)
        note = load_note(
            absolute_path=candidate,
            relative_path=relative_path,
            raw_text=raw_text,
        )
        if note is None:
            return None

        if self.state.hash_cache.seen(note.relative_path, note.content_hash):
            return None
        self.state.hash_cache.remember(note.relative_path, note.content_hash)
        return note

    def _relative_path(self, candidate: Path) -> str:
        try:
            return candidate.relative_to(self.vault_path).as_posix()
        except ValueError:
            return candidate.name

    def _is_within_watch_root(self, candidate: Path) -> bool:
        try:
            candidate.resolve().relative_to(self.watch_root.resolve())
            return True
        except ValueError:
            return False


class _WatcherEventHandler(FileSystemEventHandler):
    def __init__(self, on_path: Callable[[Path], None]) -> None:
        super().__init__()
        self._on_path = on_path

    def on_created(self, event):  # type: ignore[override]
        if not event.is_directory:
            self._on_path(Path(event.src_path))

    def on_modified(self, event):  # type: ignore[override]
        if not event.is_directory:
            self._on_path(Path(event.src_path))

    def on_moved(self, event: FileSystemMovedEvent) -> None:  # type: ignore[override]
        if not event.is_directory:
            self._on_path(Path(event.dest_path))


def build_observer(note_watcher: NoteWatcher) -> tuple[Observer, _WatcherEventHandler]:
    observer = Observer()
    handler = _WatcherEventHandler(note_watcher.enqueue)
    observer.schedule(handler, str(note_watcher.watch_root), recursive=True)
    return observer, handler
