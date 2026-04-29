# Phase 3 Prompt — SQLite Schema and Persistence

You are adding persistence to the Kanban Prompt Companion after the ingest/pipeline/Kanban manifest mechanics exist.

Do not import PromptForge’s Postgres schema. Do not create generic platform tables.

## Goal

Persist only the state required for:

```text
note discovered
note parsed
prompt package generated
prompt step generated
Kanban payload previewed
Kanban payload delivered or failed
manual retry
```

## Explicitly Rejected Persistence Patterns

Do not add:

- Postgres
- Alembic unless already chosen and absolutely necessary
- 15-table PromptForge schema
- `projects` table unless concrete need is proven
- users table
- roles table
- rulesets table
- rules table
- prompt templates table
- term dictionary table
- delivery targets table
- delivery session registry table
- processing runs table
- LLM runs table
- workflow error records table
- console runtime settings table
- secret settings table
- audit log table

## Required Database

Use SQLite.

Default path from env:

```bash
KPC_DATABASE_PATH=./data/kanban-prompt-companion.sqlite3
```

## Required Tables

Create only these tables unless a test-proven need requires one more:

```text
notes
prompt_packages
prompt_steps
deliveries
```

### notes

Fields:

```text
id TEXT PRIMARY KEY
absolute_path TEXT NOT NULL
relative_path TEXT NOT NULL
content_hash TEXT NOT NULL
title TEXT NOT NULL
frontmatter_json TEXT NOT NULL DEFAULT '{}'
raw_body TEXT NOT NULL DEFAULT ''
raw_transcript TEXT NOT NULL DEFAULT ''
status TEXT NOT NULL
watch_eligible INTEGER NOT NULL DEFAULT 1
discovered_at TEXT NOT NULL
last_seen_at TEXT NOT NULL
processed_at TEXT
error_message TEXT
```

Constraints/indexes:

- unique `relative_path`
- index `status`
- index `content_hash`

Allowed status values:

```text
discovered
skipped
parsed
generated
review_ready
delivered
failed
archived
```

### prompt_packages

Fields:

```text
id TEXT PRIMARY KEY
note_id TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE
version TEXT NOT NULL DEFAULT 'v1'
cleaned_intent TEXT NOT NULL
project_key TEXT
kanban_workspace_id TEXT
status TEXT NOT NULL
requires_review INTEGER NOT NULL DEFAULT 1
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
error_message TEXT
```

Allowed status values:

```text
draft
review_ready
approved
delivering
delivered
failed
rejected
```

### prompt_steps

Fields:

```text
id TEXT PRIMARY KEY
package_id TEXT NOT NULL REFERENCES prompt_packages(id) ON DELETE CASCADE
step_index INTEGER NOT NULL
external_task_key TEXT NOT NULL
title TEXT NOT NULL
prompt_markdown TEXT NOT NULL
base_ref TEXT
agent_id TEXT
start_in_plan_mode INTEGER NOT NULL DEFAULT 1
depends_on_step_indices_json TEXT NOT NULL DEFAULT '[]'
status TEXT NOT NULL
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

Constraints/indexes:

- unique `(package_id, step_index)`
- unique `external_task_key`
- index `package_id`
- index `status`

### deliveries

Fields:

```text
id TEXT PRIMARY KEY
package_id TEXT NOT NULL REFERENCES prompt_packages(id) ON DELETE CASCADE
kanban_workspace_id TEXT NOT NULL
request_json TEXT NOT NULL
response_json TEXT
status TEXT NOT NULL
error_message TEXT
created_at TEXT NOT NULL
delivered_at TEXT
```

Allowed status values:

```text
previewed
delivering
delivered
failed
retry_ready
```

## Required Storage Layer

Create modules equivalent to:

```text
app/storage/db.py
app/storage/schema.py
app/storage/repository.py
```

Requirements:

- initialize database on startup
- run idempotent schema creation
- no destructive migrations in MVP
- use parameterized SQL
- store JSON as text using standard library `json`
- isolate SQL from API handlers
- keep repository functions narrow and obvious

## Required Repository Operations

Implement:

```python
upsert_note_from_loaded_note(...)
mark_note_status(...)
create_prompt_package(...)
get_prompt_package(...)
list_review_packages(...)
update_prompt_step_markdown(...)
mark_package_approved(...)
create_delivery_preview(...)
mark_delivery_delivering(...)
mark_delivery_success(...)
mark_delivery_failed(...)
list_deliveries(...)
get_delivery(...)
```

Do not add generic CRUD endpoints or repository abstractions.

## Required Tests

Add tests for:

- schema initialization is idempotent
- note upsert by relative path
- content hash update
- prompt package creation with steps
- cascade delete from package to steps/deliveries if applicable
- list review packages
- update prompt markdown
- create delivery preview
- mark delivery success/failure
- JSON fields round-trip

## Migration Philosophy

For MVP, use one schema creation file/function.

Do not introduce a migration framework unless a real second schema version appears.

## Output Required

Return:

1. Schema implemented.
2. Files created/changed.
3. Repository operations implemented.
4. Tests added and run.
5. Confirmation that no rejected PromptForge tables were added.
6. Any schema tradeoffs or open questions.
