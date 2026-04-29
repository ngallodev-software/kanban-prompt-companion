# Kanban Prompt Companion

Kanban Prompt Companion is a focused local app that turns Obsidian markdown notes in a configured watch folder into reviewed Kanban-ready tasks.

Flow:

`Obsidian note -> cleaned intent -> prompt package -> human review -> Kanban delivery`

This repo stays intentionally small and focused on note-to-task delivery.

## Screenshots

### Intake
![Intake view](docs/screenshots/intake.png)

### Review
![Review view](docs/screenshots/review.png)

### Deliveries
![Deliveries view](docs/screenshots/deliveries.png)

### Settings
![Settings view](docs/screenshots/settings.png)

## Features

- Watches a vault folder for markdown notes in the configured intake directory
- Extracts and cleans note intent into a versioned prompt package
- Human-in-the-loop review/edit step before delivery
- Kanban preview + delivery through supported API surface
- Delivery history and retry flow

## Architecture

- Backend: FastAPI + SQLite
- Frontend: React + Vite + Tailwind
- Delivery target: Kanban integration endpoints (no direct board file writes)

## Kanban Compatibility

This companion supports both:

- stock Kanban instances
- custom/forked Kanban instances with extended endpoints

When available, it uses these endpoints:

- `projects.list`
- `projects.add`
- `workspace.getState`
- `workspace.importTasks`
- `workspace.upsertTaskByExternalKey` (when available in your Kanban fork)

Delivery behavior is capability-aware:

1. For single-step packages, it prefers `workspace.upsertTaskByExternalKey` when supported.
2. Otherwise it uses `workspace.importTasks`.
3. If `workspace.importTasks` is not present on the target instance, it falls back to built-in task creation via standard tRPC task-create procedures.

This means the companion works against stock or custom Kanban, with graceful downgrade behavior.

If you want the endpoint-enabled Kanban build, use this fork branch:

- <https://github.com/ngallodev-software/kanban/tree/fork/feature-requests/roll-up>

Upstream Kanban project:

- <https://github.com/cline/kanban>

## Quick Start

### 1) Clone and configure

```bash
cp .env.example .env
```

Update `.env` with your local vault and Kanban endpoint settings.

### 2) Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --host 127.0.0.1 --port 8091 --reload
```

### 3) Frontend

```bash
cd web
npm install
npm run dev -- --host 127.0.0.1 --port 5178
```

Open `http://127.0.0.1:5178`.

## Testing

Backend:

```bash
pytest -q
```

Frontend:

```bash
cd web
npm test -- --run
npm run typecheck
npm run build
```

Backend integration path coverage includes both:

- custom endpoint path (`workspace.importTasks` / `workspace.upsertTaskByExternalKey`)
- stock fallback path (built-in tRPC task creation when import endpoint is missing)

## Build a Single Executable

This repo includes a one-file executable build using PyInstaller.

Versioning starts at `0.0.1` and is built into the binary name.

Build:

```bash
bash scripts/build_executable.sh
```

Output:

- `dist/kanban-prompt-companion-<version>-<os>-<arch>`

You can also check the app version directly:

```bash
python -m app.cli --version
```

## Scope and Non-Goals

This project explicitly excludes platform-heavy features like auth systems, admin dashboards, multi-target routing, and direct Kanban state-file mutation.

See [NON_GOALS.md](./NON_GOALS.md).

## Runbook

Operational and debugging details are in [RUNBOOK.md](./RUNBOOK.md).

## License

MIT — see [LICENSE](./LICENSE).
