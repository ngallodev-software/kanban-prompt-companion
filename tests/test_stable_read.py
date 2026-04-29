from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ingest.stable_read import StableReadTimeoutError, read_stable_text


def test_read_stable_text_waits_for_stable_size_and_mtime(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("stable", encoding="utf-8")

    clock = {"t": 0.0, "i": 0}

    def monotonic_fn() -> float:
        return clock["t"]

    def sleep_fn(_: float) -> None:
        clock["t"] += 0.1

    stats = [
        SimpleNamespace(st_size=1, st_mtime_ns=1),
        SimpleNamespace(st_size=2, st_mtime_ns=2),
        SimpleNamespace(st_size=2, st_mtime_ns=2),
    ]

    def stat_fn(_: Path) -> SimpleNamespace:
        index = min(clock["i"], len(stats) - 1)
        clock["i"] += 1
        return stats[index]

    assert read_stable_text(
        note,
        timeout_seconds=1.0,
        poll_interval_seconds=0.01,
        stat_fn=stat_fn,
        sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn,
    ) == "stable"


def test_read_stable_text_times_out_when_never_stable(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("unstable", encoding="utf-8")

    clock = {"t": 0.0}

    def monotonic_fn() -> float:
        return clock["t"]

    def sleep_fn(_: float) -> None:
        clock["t"] += 0.1

    def stat_fn(_: Path) -> SimpleNamespace:
        clock["t"] += 0.01
        return SimpleNamespace(st_size=int(clock["t"] * 1000), st_mtime_ns=int(clock["t"] * 1000000))

    with pytest.raises(StableReadTimeoutError):
        read_stable_text(
            note,
            timeout_seconds=0.2,
            poll_interval_seconds=0.01,
            stat_fn=stat_fn,
            sleep_fn=sleep_fn,
            monotonic_fn=monotonic_fn,
        )
