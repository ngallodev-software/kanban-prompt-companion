# Phase 7 Prompt — End-to-End Hardening and Runbook

You are hardening the Kanban Prompt Companion and proving the MVP loop works.

## Goal

Demonstrate this exact flow:

```text
one Obsidian-style markdown note
→ note detected
→ transcript parsed
→ speech artifacts cleaned
→ prompt package generated
→ user can review/edit
→ Kanban payload previewed
→ Kanban task delivered
→ delivery result stored
```

## Required E2E Fixture

Create a realistic test note fixture:

```markdown
---
title: Parser pipeline voice note
status: new
watch_eligible: true
---

## Control
project is kanban
workspace is kanban
harness is codex
base ref is main

## Transcript
Um, I need you to add a simple parser for the note intake flow. It should read the front matter, uh, pull out the transcript section, and make sure we do not process notes marked processed. Also add tests. Do not change unrelated Kanban files.
```

The resulting prompt should preserve intent and remove obvious speech artifacts without losing constraints.

## Backend Integration Tests

Add tests for:

1. watcher startup scan discovers fixture note
2. note parser extracts frontmatter/control/transcript
3. cleanup removes filler but preserves technical terms
4. prompt package generated with stable external task key
5. Kanban manifest preview matches expected shape
6. mocked Kanban delivery records success
7. mocked Kanban failure records useful error
8. retry uses current prompt step content

## API Integration Tests

Add tests for:

- `/api/intake`
- `/api/review`
- `/api/packages/{id}`
- step edit
- Kanban preview
- Kanban deliver
- delivery retry

## Frontend Integration Tests

Add tests for:

- user opens review screen
- user edits prompt
- user previews payload
- user delivers
- success displayed
- failure/retry displayed

## Manual Local Runbook

Create `RUNBOOK.md` with:

### Prerequisites

- Python version
- Node version
- Kanban running location/port
- Obsidian vault path

### Setup

Commands to install backend and frontend dependencies.

### Configuration

Explain `.env` values:

```bash
KPC_VAULT_PATH=
KPC_WATCH_FOLDER=
KPC_DATABASE_PATH=
KPC_KANBAN_BASE_URL=
KPC_KANBAN_WORKSPACE_ID=
```

### Run Backend

Command to start API/watcher.

### Run Frontend

Command to start frontend.

### E2E Smoke Test

Steps:

1. Place fixture note in watch folder.
2. Confirm note appears in intake.
3. Open review screen.
4. Preview Kanban payload.
5. Deliver to Kanban.
6. Confirm card appears in Kanban.
7. Confirm delivery status is recorded.

### Troubleshooting

Include:

- Kanban unreachable
- missing workspace ID
- malformed frontmatter
- note skipped due to status
- empty transcript
- delivery failed
- duplicate external task key

## Scope Hardening Check

Verify no forbidden systems were added:

- no Postgres
- no n8n
- no LLM provider router
- no tmux/session dispatch
- no target registry
- no dashboard/metrics
- no role switcher
- no template/rules/dictionary admin UI

## Output Required

Return:

1. E2E fixture created.
2. Tests added.
3. Runbook created.
4. Commands run and results.
5. Manual smoke-test steps and whether completed.
6. Any remaining MVP blockers.
