# Master Phase Implementation Prompt — Kanban Prompt Companion

You are coordinating implementation of a new minimalist Kanban Prompt Companion.

This is **not** PromptForge v2. This is a new, smaller companion app whose only job is:

```text
Obsidian markdown voice note
→ cleaned transcript / cleaned intent
→ generated prompt package
→ human review
→ Kanban task delivery
```

## Source Projects Available

You may inspect these existing repos for salvage only:

- Backend source to salvage cautiously: `prompt-forge`
- Frontend source to salvage cautiously: `prompt-forge-console`
- Kanban integration target: modified `kanban` fork

## Non-Negotiable Scope Boundary

Do not rebuild the PromptForge platform.

Do not add:

- Postgres
- n8n
- LLM provider routing
- tmux/session delivery
- multi-target delivery registry
- role switcher
- users/roles/auth system
- dashboard/metrics/SLA pages
- rule marketplace
- template marketplace
- dictionary management UI
- logs/error fingerprint UI
- pipeline visualization
- generic admin console CRUD
- large settings admin page
- direct writes to Kanban JSON state

## Implementation Principle

Salvage mechanics, not architecture.

Approved salvage areas:

- watcher startup scan, debounce, hidden/temp-file filtering, hash dedupe
- markdown/frontmatter parsing, rewritten around `python-frontmatter`
- section extraction for `## Control` and `## Transcript`
- deterministic cleanup/directive concepts, rewritten for this app
- versioned Pydantic prompt package contract
- file-based Jinja rendering
- Kanban manifest builder and Kanban client logic, stripped of PromptForge imports
- minimal UI primitives only
- hardened markdown preview
- stripped Kanban preview/apply flow
- tiny API client and typed error helpers
- Kanban-style visual treatment

## Required Phase Flow

Execute phases in order. Do not skip ahead. Each phase must end with tests or verification notes.

### Phase 1 — Project Skeleton and Boundaries

Use `01_PROJECT_SKELETON_AND_BOUNDARIES.md`.

Goal: create the new project structure, dependency baseline, config files, non-goals, and empty app shell.

Do not implement pipeline logic yet.

### Phase 2 — Backend Salvage Port: Ingest and Pipeline Mechanics

Use `02_BACKEND_SALVAGE_PORT_INGEST_AND_PIPELINE.md`.

Goal: port only approved backend mechanics through Kanban manifest/client, without persistence-heavy architecture.

Do not implement SQLite schema yet except temporary in-memory structures needed for tests.

### Phase 3 — SQLite Schema and Persistence

Use `03_SQLITE_SCHEMA_AND_PERSISTENCE.md`.

Goal: persist only the state proven necessary by Phase 2.

Do not add Postgres-style normalized PromptForge tables.

### Phase 4 — Backend API and Kanban Delivery Flow

Use `04_BACKEND_API_AND_KANBAN_DELIVERY.md`.

Goal: expose the minimal API for queue, review, preview, delivery, retry, and health.

Do not add broad admin APIs.

### Phase 5 — Frontend Style Alignment with Kanban

Use `05_FRONTEND_STYLE_ALIGNMENT_WITH_KANBAN.md`.

Goal: inspect the modified Kanban app’s visual conventions and create a matching but separate companion UI foundation.

Do not copy PromptForge Console’s admin shell.

### Phase 6 — Minimal Review UI Implementation

Use `06_MINIMAL_REVIEW_UI_IMPLEMENTATION.md`.

Goal: build the smallest frontend that supports intake, review/preview/edit, deliver, and delivery status.

### Phase 7 — End-to-End Hardening and Runbook

Use `07_E2E_TEST_HARDENING_AND_RUNBOOK.md`.

Goal: prove one real note can produce one reviewed Kanban task package and document how to run/debug it.

### Phase 8 — Scope Guardrail Review

Use `08_SCOPE_GUARDRAIL_REVIEW.md`.

Goal: audit the implementation for PromptForge platform creep before calling MVP complete.

## State and Data Model Target

Do not design schema until Phase 3, but the expected upper bound is:

```text
notes
prompt_packages
prompt_steps
deliveries
```

No `projects` table unless a concrete need is proven. No rules table. No template table. No delivery target table. No users table.

## Kanban Integration Target

Prefer the modified Kanban app’s supported tRPC integration surface:

- `projects.list`
- `projects.add`
- `workspace.getState`
- `workspace.importTasks`
- `workspace.upsertTaskByExternalKey` if available after the Kanban-side addition

Represent prompt chains as multiple Kanban tasks with stable `externalTaskKey` values and links/dependencies where supported.

Do not write directly to Kanban’s `board.json` or `sessions.json`.

## Required Output After Each Phase

For each phase, report:

1. Files created/changed.
2. What was deliberately not implemented.
3. Tests run and results.
4. Any unresolved questions.
5. Whether the implementation stayed inside the non-goals.

## Failure Rules

If a desired feature requires pulling in rejected PromptForge architecture, do not implement it. Stop and propose the smallest alternative.

If the frontend begins to require a dashboard, role switcher, global store, complex admin shell, or multi-page settings system, stop and simplify.

If the backend begins to require Postgres, n8n, LLM routing, or multi-target delivery, stop and simplify.
