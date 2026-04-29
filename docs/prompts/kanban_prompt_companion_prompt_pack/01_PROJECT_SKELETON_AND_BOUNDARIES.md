# Phase 1 Prompt — Project Skeleton and Boundaries

You are creating the initial skeleton for the new minimalist Kanban Prompt Companion.

This is a new project. Do not refactor `prompt-forge`. Do not refactor `prompt-forge-console`. Do not modify `kanban` in this phase.

## Goal

Create a clean new project structure that supports:

```text
Obsidian markdown voice note
→ cleaned transcript / cleaned intent
→ generated prompt package
→ human review
→ Kanban task delivery
```

## Required Source Inspection

Before creating files, inspect:

- `prompt-forge` only for dependency choices and salvage source paths
- `prompt-forge-console` only for minimal frontend dependency/style reference
- modified `kanban` only for expected sibling-app structure and styling conventions

Do not copy large code in this phase.

## Required Project Structure

Create or prepare a structure equivalent to:

```text
kanban-prompt-companion/
  README.md
  NON_GOALS.md
  pyproject.toml
  .env.example
  app/
    __init__.py
    main.py
    config.py
    contracts.py
    ingest/
      __init__.py
    pipeline/
      __init__.py
    kanban/
      __init__.py
    storage/
      __init__.py
  templates/
    prompt_package.md.j2
  tests/
    fixtures/
  web/
    package.json
    vite.config.ts
    index.html
    src/
      main.tsx
      App.tsx
      index.css
      api/
      components/
      features/
```

If the actual repo already exists, adapt this structure without breaking existing working files.

## Backend Dependency Baseline

Prefer a minimal Python backend.

Allowed dependencies:

- `fastapi`
- `uvicorn`
- `pydantic`
- `watchdog`
- `python-frontmatter`
- `jinja2`
- `httpx`
- `pytest`
- optional: `mdformat`
- optional: `rapidfuzz`

Avoid:

- `psycopg`
- Postgres drivers
- `libtmux`
- `cryptography` for DB secret management
- LLM provider SDKs
- n8n clients
- workflow engines

## Frontend Dependency Baseline

Allowed dependencies:

- React
- Vite
- TypeScript
- Tailwind
- `@tanstack/react-query`
- `clsx`
- `tailwind-merge`
- minimal Radix primitives only if actually used
- optional `lucide-react`

Avoid unless proven necessary:

- Zustand
- React Hook Form
- Zod on frontend
- Recharts
- cmdk
- react-window
- broad Radix package import set
- PromptForge Console shell dependencies

## Required Documents

Create `NON_GOALS.md` with explicit exclusions:

```text
This project does not manage users.
This project does not manage roles.
This project does not manage arbitrary delivery targets.
This project does not execute coding agents.
This project does not replace Kanban.
This project does not provide a rules marketplace.
This project does not provide a template marketplace.
This project does not require n8n.
This project does not require Postgres.
This project does not provide dashboards, SLA metrics, or throughput charts.
This project does not store secrets in a database.
```

Create `README.md` that states:

- what the app does
- what it does not do
- expected local runtime
- expected Kanban integration mode
- expected Obsidian vault/input folder

Create `.env.example` with only:

```bash
KPC_VAULT_PATH=/path/to/obsidian/vault
KPC_WATCH_FOLDER=Inbox/Voice
KPC_PROCESSED_FOLDER=Processed/Voice
KPC_DATABASE_PATH=./data/kanban-prompt-companion.sqlite3
KPC_KANBAN_BASE_URL=http://127.0.0.1:3484
KPC_KANBAN_WORKSPACE_ID=
KPC_TEMPLATE_DIR=./templates
KPC_BIND_HOST=127.0.0.1
KPC_BIND_PORT=8091
```

Do not include API keys or LLM provider settings.

## Backend Skeleton Requirements

Create a minimal FastAPI app with:

- `GET /health`
- config loading from environment
- no database yet, unless needed only as a placeholder path

## Frontend Skeleton Requirements

Create a minimal Vite/React app that renders:

- title: Kanban Prompt Companion
- subtitle: Obsidian note → prompt package → Kanban task
- placeholder panels for Intake, Review, Deliveries

Do not build the real UI in this phase.

## Tests / Verification

Add or verify:

- backend imports cleanly
- `GET /health` returns `{ "ok": true }`
- frontend builds or at least starts under Vite
- no rejected dependencies are added

## Output Required

Return:

1. Files created/changed.
2. Dependency list added.
3. Commands run.
4. Confirmation that rejected systems were not added.
5. Any issues or assumptions.
