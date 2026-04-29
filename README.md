# Kanban Prompt Companion

Kanban Prompt Companion is a small local app that watches an Obsidian vault for voice-note markdown, turns the note into a cleaned prompt package, lets a human review the result, and prepares delivery into Kanban tasks.

It is intentionally not a platform. It does not manage users, roles, arbitrary delivery targets, dashboards, or any of the heavier PromptForge machinery.

## Local runtime

- Python backend: FastAPI on `127.0.0.1:8091`
- Frontend: Vite React app in `web/`
- Input source: an Obsidian vault folder on the local machine

## Integration mode

The companion is meant to hand off reviewed prompt packages into the modified Kanban app through its supported integration surface. It should not write directly to Kanban board state files.

## Vault and folders

- Vault path: configured by `KPC_VAULT_PATH`
- Watch folder: configured by `KPC_WATCH_FOLDER`
- Processed folder: configured by `KPC_PROCESSED_FOLDER`

## Out of scope

See [NON_GOALS.md](./NON_GOALS.md) for the full boundary list.
