from __future__ import annotations

import os
import sys
from pathlib import Path

from pydantic import BaseModel, HttpUrl


class AppConfig(BaseModel):
    vault_path: Path
    watch_folder: str
    processed_folder: str
    database_path: Path
    kanban_base_url: HttpUrl
    kanban_workspace_id: str
    template_dir: Path
    bind_host: str = "127.0.0.1"
    bind_port: int = 8091


def load_config() -> AppConfig:
    """Load the app configuration from environment variables."""
    template_dir = os.getenv("KPC_TEMPLATE_DIR")
    if template_dir:
        resolved_template_dir = Path(template_dir).expanduser()
    elif getattr(sys, "_MEIPASS", None):
        resolved_template_dir = Path(getattr(sys, "_MEIPASS")) / "templates"
    else:
        resolved_template_dir = Path(__file__).resolve().parents[1] / "templates"

    return AppConfig(
        vault_path=Path(os.getenv("KPC_VAULT_PATH", "")).expanduser(),
        watch_folder=os.getenv("KPC_WATCH_FOLDER", "Inbox/Voice"),
        processed_folder=os.getenv("KPC_PROCESSED_FOLDER", "Processed/Voice"),
        database_path=Path(os.getenv("KPC_DATABASE_PATH", "./data/kanban-prompt-companion.sqlite3")).expanduser(),
        kanban_base_url=os.getenv("KPC_KANBAN_BASE_URL", "http://127.0.0.1:3484"),
        kanban_workspace_id=os.getenv("KPC_KANBAN_WORKSPACE_ID", ""),
        template_dir=resolved_template_dir,
        bind_host=os.getenv("KPC_BIND_HOST", "127.0.0.1"),
        bind_port=int(os.getenv("KPC_BIND_PORT", "8091")),
    )
