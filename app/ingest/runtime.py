from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, Thread

from watchdog.observers import Observer

from app.ingest.watcher import NoteWatcher, build_observer
from app.pipeline.cleanup import cleanup_transcript
from app.pipeline.directives import parse_directives
from app.pipeline.render import build_prompt_package
from app.storage import create_prompt_package, upsert_note_from_loaded_note

logger = logging.getLogger(__name__)


@dataclass
class NoteIngestRuntime:
    connection: sqlite3.Connection
    template_dir: Path
    watcher: NoteWatcher
    observer: Observer | None = None
    worker: Thread | None = None
    stop_event: Event = field(default_factory=Event)
    started: bool = False

    def start(self) -> None:
        if self.started:
            return
        self.started = True

        watch_root = self.watcher.watch_root
        watch_root.mkdir(parents=True, exist_ok=True)

        self._process_startup_scan()

        if watch_root.exists():
            self.observer, _handler = build_observer(self.watcher)
            self.observer.start()
            self.worker = Thread(target=self._run, name="kanban-prompt-companion-watcher", daemon=True)
            self.worker.start()
            logger.info("watcher started for %s", watch_root)

    def stop(self) -> None:
        self.stop_event.set()
        if self.observer is not None:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.observer = None
        if self.worker is not None:
            self.worker.join(timeout=5.0)
            self.worker = None
        logger.info("watcher stopped")

    def _run(self) -> None:
        while not self.stop_event.wait(self.watcher.poll_interval_seconds):
            for note_path in self.watcher.drain_ready():
                self._process_path(note_path, source="event")

    def _process_startup_scan(self) -> None:
        for note_path in self.watcher.startup_scan():
            self._process_path(note_path, source="startup")

    def _process_path(self, note_path: str | Path, *, source: str) -> None:
        try:
            loaded_note = self.watcher.process_path(note_path)
            if loaded_note is None:
                return

            stored_note = upsert_note_from_loaded_note(self.connection, loaded_note)
            directives = parse_directives(loaded_note.control_text)
            cleanup_result = cleanup_transcript(loaded_note.transcript_text)
            package = build_prompt_package(
                note=loaded_note,
                directives=directives,
                cleanup_result=cleanup_result,
                template_dir=self.template_dir,
            )
            stored_package = create_prompt_package(self.connection, stored_note.id, package)
            logger.info(
                "processed %s note=%s package=%s steps=%s",
                source,
                stored_note.relative_path,
                stored_package.id,
                len(stored_package.steps),
            )
        except Exception:
            logger.exception("failed processing %s note path %s", source, note_path)
