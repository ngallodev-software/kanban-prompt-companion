from __future__ import annotations

import sqlite3
from pathlib import Path

from app.storage.schema import initialize_schema


def connect_database(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    initialize_schema(connection)
    return connection
