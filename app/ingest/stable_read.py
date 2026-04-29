from __future__ import annotations

import time
from pathlib import Path
from typing import Callable


class StableReadTimeoutError(TimeoutError):
    pass


def read_stable_text(
    path: str | Path,
    *,
    timeout_seconds: float = 5.0,
    poll_interval_seconds: float = 0.1,
    encoding: str = "utf-8",
    stat_fn: Callable[[Path], object] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    monotonic_fn: Callable[[], float] | None = None,
) -> str:
    candidate = Path(path)
    stat_fn = stat_fn or Path.stat
    sleep_fn = sleep_fn or time.sleep
    monotonic_fn = monotonic_fn or time.monotonic
    deadline = monotonic_fn() + timeout_seconds
    previous_signature: tuple[int, int] | None = None

    while monotonic_fn() <= deadline:
        stat_result = stat_fn(candidate)
        signature = (int(getattr(stat_result, "st_size")), int(getattr(stat_result, "st_mtime_ns")))
        if signature == previous_signature:
            return candidate.read_text(encoding=encoding)
        previous_signature = signature
        sleep_fn(poll_interval_seconds)

    raise StableReadTimeoutError(f"file never stabilized: {candidate}")
