from __future__ import annotations

import sqlite3


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(_SCHEMA_SQL)
    connection.commit()


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS notes (
  id TEXT PRIMARY KEY,
  absolute_path TEXT NOT NULL,
  relative_path TEXT NOT NULL UNIQUE,
  content_hash TEXT NOT NULL,
  title TEXT NOT NULL,
  frontmatter_json TEXT NOT NULL DEFAULT '{}',
  raw_body TEXT NOT NULL DEFAULT '',
  raw_transcript TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL CHECK (status IN (
    'discovered',
    'skipped',
    'parsed',
    'generated',
    'review_ready',
    'delivered',
    'failed',
    'archived'
  )),
  watch_eligible INTEGER NOT NULL DEFAULT 1 CHECK (watch_eligible IN (0, 1)),
  discovered_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  processed_at TEXT,
  error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_notes_status ON notes(status);
CREATE INDEX IF NOT EXISTS idx_notes_content_hash ON notes(content_hash);

CREATE TABLE IF NOT EXISTS prompt_packages (
  id TEXT PRIMARY KEY,
  note_id TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  version TEXT NOT NULL DEFAULT 'v1',
  cleaned_intent TEXT NOT NULL,
  project_key TEXT,
  kanban_workspace_id TEXT,
  status TEXT NOT NULL CHECK (status IN (
    'draft',
    'review_ready',
    'approved',
    'delivering',
    'delivered',
    'failed',
    'rejected'
  )),
  requires_review INTEGER NOT NULL DEFAULT 1 CHECK (requires_review IN (0, 1)),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompt_packages_note_id ON prompt_packages(note_id);
CREATE INDEX IF NOT EXISTS idx_prompt_packages_status ON prompt_packages(status);

CREATE TABLE IF NOT EXISTS prompt_steps (
  id TEXT PRIMARY KEY,
  package_id TEXT NOT NULL REFERENCES prompt_packages(id) ON DELETE CASCADE,
  step_index INTEGER NOT NULL,
  external_task_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  prompt_markdown TEXT NOT NULL,
  base_ref TEXT,
  agent_id TEXT,
  start_in_plan_mode INTEGER NOT NULL DEFAULT 1 CHECK (start_in_plan_mode IN (0, 1)),
  depends_on_step_indices_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL CHECK (status IN (
    'draft',
    'approved',
    'delivered',
    'failed'
  )),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (package_id, step_index)
);

CREATE INDEX IF NOT EXISTS idx_prompt_steps_package_id ON prompt_steps(package_id);
CREATE INDEX IF NOT EXISTS idx_prompt_steps_status ON prompt_steps(status);

CREATE TABLE IF NOT EXISTS deliveries (
  id TEXT PRIMARY KEY,
  package_id TEXT NOT NULL REFERENCES prompt_packages(id) ON DELETE CASCADE,
  kanban_workspace_id TEXT NOT NULL,
  request_json TEXT NOT NULL,
  response_json TEXT,
  status TEXT NOT NULL CHECK (status IN (
    'previewed',
    'delivering',
    'delivered',
    'failed',
    'retry_ready'
  )),
  error_message TEXT,
  created_at TEXT NOT NULL,
  delivered_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_deliveries_package_id ON deliveries(package_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
"""
