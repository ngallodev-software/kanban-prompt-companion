# Kanban Prompt Companion Runbook

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- Kanban app running at `KPC_KANBAN_BASE_URL`
- Obsidian vault path available locally

## Setup

Backend:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

Frontend:

```bash
cd web
npm install
```

## Configuration

Set the backend environment values before starting the service:

```bash
KPC_VAULT_PATH=/path/to/vault
KPC_WATCH_FOLDER=Inbox/Voice
KPC_DATABASE_PATH=./data/kanban-prompt-companion.sqlite3
KPC_KANBAN_BASE_URL=http://127.0.0.1:3484
KPC_KANBAN_WORKSPACE_ID=kanban
```

Optional local overrides:

```bash
KPC_PROCESSED_FOLDER=Processed/Voice
KPC_TEMPLATE_DIR=./templates
KPC_BIND_HOST=127.0.0.1
KPC_BIND_PORT=8091
```

## Run Backend

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8091
```

## Run Frontend

```bash
cd web
npm run dev -- --host 127.0.0.1 --port 5173
```

## E2E Smoke Test

1. Place `tests/fixtures/parser_pipeline_voice_note.md` into the watched Obsidian folder.
2. Confirm the note appears in `/api/intake`.
3. Open the review screen in the web app.
4. Edit the prompt step if needed.
5. Preview the Kanban payload.
6. Deliver the package to Kanban.
7. Confirm the task appears in Kanban.
8. Confirm the delivery is stored in `/api/deliveries`.

## Troubleshooting

- Kanban unreachable: verify `KPC_KANBAN_BASE_URL` and the Kanban app are running.
- Missing workspace ID: set `KPC_KANBAN_WORKSPACE_ID` or the note control `workspace` value.
- Malformed frontmatter: fix the note YAML block and re-save the file.
- Note skipped due to status: ensure `status: new` and `watch_eligible: true`.
- Empty transcript: make sure the `## Transcript` section has content.
- Delivery failed: inspect `/api/deliveries/{id}` for the stored error message.
- Duplicate external task key: rename the note or reset the existing package before retrying.

## Scope Guardrails

The phase 7 hardening pass keeps the app inside the agreed boundary:

- no Postgres
- no n8n
- no LLM provider router
- no tmux/session dispatch
- no target registry
- no dashboard or metrics pages
- no role switcher
- no template/rules/dictionary admin UI
