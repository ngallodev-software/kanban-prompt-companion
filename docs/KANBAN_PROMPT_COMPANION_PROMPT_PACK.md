# Minimal Kanban Voice-Prompt Companion — Prompt Pack

**Purpose:** Implementation prompts for building a minimal Obsidian voice-note-to-Kanban prompt companion without repeating PromptForge’s platform complexity.

**How to use:** Feed these prompts to Codex/Claude agents one at a time. Each prompt is scoped to produce a concrete result and avoid broad redesign.

---

## Prompt 1 — Create the New Repository Skeleton

```md
You are creating a new minimal companion app for a modified Kanban system.

Working name: `kanban-prompt-companion`.

Context:
- This is not PromptForge v2.
- It is a small local app that watches Obsidian speech-to-text notes, compiles high-quality AI coding prompts, shows them for review, and sends approved prompts to Kanban.
- The frontend should visually match the existing Kanban app styling conventions, but this is a separate sibling app.
- Do not copy protected branding, logos, or proprietary assets.
- Do not implement users, roles, dashboards, n8n, Postgres, LLM provider routing, template marketplaces, or rule marketplaces.

Create a new repository skeleton with:

Backend:
- Python 3.11+
- FastAPI
- SQLite
- watchdog
- python-frontmatter
- PyYAML
- Jinja2
- httpx
- pytest

Frontend:
- React
- Vite
- TypeScript
- Tailwind CSS
- Radix/shadcn-style minimal component primitives only where useful
- Lucide icons

Top-level structure:

```text
kanban-prompt-companion/
  backend/
    app/
      main.py
      config.py
      db.py
      models.py
      watcher.py
      note_parser.py
      compiler.py
      kanban_client.py
      api/
        notes.py
        packages.py
        deliveries.py
        settings.py
    tests/
    pyproject.toml
  frontend/
    src/
      main.tsx
      App.tsx
      api/
      components/
      pages/
      styles/
    package.json
    vite.config.ts
    tailwind.config.ts
  rules/
    global.yaml
    projects/
      example.yaml
  templates/
    coding_task.md.j2
  samples/
    notes/
      sample_voice_note.md
  docs/
    NON_GOALS.md
    ARCHITECTURE.md
  .env.example
  README.md
```

Required docs:
- `docs/NON_GOALS.md` must explicitly forbid n8n, Postgres, multi-user roles, role switcher, metrics dashboards, multi-target delivery registry, template/rules CRUD, and direct Kanban JSON writes.
- `README.md` must describe the narrow loop: Obsidian note → cleaned intent → prompt package → review → Kanban task.

Do not implement full behavior yet. Create the skeleton, dependency files, sample config, and placeholder endpoints.

Run formatting and tests if available.

Output:
1. Files created.
2. How to run backend.
3. How to run frontend.
4. What is intentionally not implemented.
```

---

## Prompt 2 — Inspect Kanban Styling and Produce Frontend Style Guide

```md
You are inspecting the modified Kanban app so the new companion frontend can visually match it.

Context:
- The new app is separate and should not claim to be Kanban.
- The goal is visual continuity: same local-app feel, similar Tailwind conventions, spacing, cards, badges, muted borders, typography, and dark/light behavior if present.
- Do not copy protected branding, logos, or proprietary assets.
- Do not modify files.

Inspect the Kanban frontend source and produce a markdown style guide for the companion app.

Look for:
- Tailwind version/configuration
- CSS entry files
- theme variables/tokens
- app shell layout
- board/card styling
- buttons
- inputs
- selects
- badges/status indicators
- dialog/modal patterns
- empty/loading/error states
- typography
- spacing/radius/shadow conventions
- dark mode behavior
- component directories to mimic conceptually

Output file:

`docs/KANBAN_STYLE_COMPATIBILITY_GUIDE.md`

Include:
1. Exact Kanban file paths inspected.
2. Recommended companion layout.
3. Recommended Tailwind classes/tokens to reuse conceptually.
4. Components the companion needs.
5. Components it should avoid.
6. A short “do not impersonate/copy branding” note.

Do not create implementation code in this prompt.
```

---

## Prompt 3 — Implement SQLite Schema and Database Layer

```md
You are implementing the minimal SQLite data layer for `kanban-prompt-companion`.

Do not add Postgres.
Do not add migrations framework complexity unless absolutely necessary.
Do not add users, roles, organizations, workspaces table, target registry, template DB, rules DB, or audit tables.

Implement:

Tables:
- notes
- prompt_packages
- prompt_steps
- deliveries

Schema requirements:

notes:
- id TEXT PRIMARY KEY
- path TEXT UNIQUE NOT NULL
- relative_path TEXT NOT NULL
- content_hash TEXT NOT NULL
- title TEXT
- raw_markdown TEXT NOT NULL
- raw_transcript TEXT
- frontmatter_json TEXT
- status TEXT NOT NULL
- detected_project_key TEXT
- discovered_at TEXT NOT NULL
- processed_at TEXT
- error TEXT

prompt_packages:
- id TEXT PRIMARY KEY
- note_id TEXT NOT NULL REFERENCES notes(id)
- title TEXT NOT NULL
- cleaned_intent TEXT NOT NULL
- summary TEXT
- target_project_key TEXT
- target_workspace_id TEXT
- target_repository_path TEXT
- target_harness TEXT
- status TEXT NOT NULL
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL
- error TEXT

prompt_steps:
- id TEXT PRIMARY KEY
- package_id TEXT NOT NULL REFERENCES prompt_packages(id)
- step_index INTEGER NOT NULL
- external_task_key TEXT UNIQUE NOT NULL
- title TEXT NOT NULL
- prompt_markdown TEXT NOT NULL
- base_ref TEXT
- target_harness TEXT
- start_in_plan_mode INTEGER NOT NULL DEFAULT 1
- auto_review_enabled INTEGER NOT NULL DEFAULT 0
- auto_review_mode TEXT
- depends_on_step_ids_json TEXT
- status TEXT NOT NULL
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL

deliveries:
- id TEXT PRIMARY KEY
- package_id TEXT NOT NULL REFERENCES prompt_packages(id)
- kanban_workspace_id TEXT NOT NULL
- kanban_base_url TEXT NOT NULL
- method TEXT NOT NULL
- request_json TEXT NOT NULL
- response_json TEXT
- status TEXT NOT NULL
- error TEXT
- created_at TEXT NOT NULL
- delivered_at TEXT

Implement:
- connection helper
- schema initialization
- small repository functions for insert/read/update
- tests for schema creation and basic CRUD

Use simple Python dataclasses or Pydantic models. Keep the layer boring.

Output:
1. Files changed.
2. Schema summary.
3. Test command and result.
```

---

## Prompt 4 — Implement Obsidian Note Parser and Watcher

```md
Implement the minimal Obsidian markdown note watcher and parser.

Requirements:
- Watch configured vault path + voice inbox folder.
- Only process `.md` files.
- Wait until file content is stable before reading.
- Parse YAML frontmatter and body using `python-frontmatter`.
- Compute content hash.
- Skip unchanged files already present with same hash.
- Store new/changed notes in SQLite `notes` table.
- Extract raw transcript from:
  1. `transcript` frontmatter key if present
  2. otherwise note body
- Preserve raw markdown and frontmatter JSON.

Do not:
- move files yet
- modify source notes yet
- call Kanban yet
- call LLMs
- emit webhooks
- add n8n

Add tests using temporary directories:
- new markdown file is ingested
- unchanged file is skipped
- changed file updates/reprocesses safely
- frontmatter transcript is preferred over body
- body fallback works

Output:
1. Files changed.
2. Watcher behavior.
3. Parser behavior.
4. Test command and result.
```

---

## Prompt 5 — Implement Deterministic Transcript Cleanup and Route Detection

```md
Implement deterministic transcript cleanup and route detection.

Goal:
Convert speech-to-text transcript text into cleaned intent without using an LLM.

Inputs:
- raw transcript text
- note frontmatter
- global rules YAML
- project rules YAML files

Implement cleanup:
- remove common filler words: um, uh, ah, like, you know, I mean, sort of, kind of, basically, actually when used as filler
- normalize whitespace
- normalize repeated punctuation
- preserve code terms, file paths, command names, package names, and identifiers
- preserve quoted text and fenced code blocks
- trim rambling open/close phrases where safe

Implement route detection:
Priority order:
1. explicit frontmatter: `project`, `target_project`, `workspace_id`, `harness`, `base_ref`
2. inline speech directives such as “project is kanban”, “target harness is codex”, “base ref is main”
3. project rule markers from `rules/projects/*.yaml`
4. default config

Output should include:
- cleaned_intent
- detected_project_key
- target_workspace_id
- target_harness
- base_ref
- confidence: high | medium | low
- ambiguity_notes[]

Do not add a generic rule engine.
Do not add database-backed rules.
Do not add rules CRUD.

Add tests:
- filler removal
- code/path preservation
- frontmatter directive priority
- inline directive parsing
- project marker fallback
- low-confidence ambiguity case

Output:
1. Files changed.
2. Cleanup rules implemented.
3. Route detection behavior.
4. Test command and result.
```

---

## Prompt 6 — Implement Prompt Compiler and File-Based Templates

```md
Implement the prompt compiler.

Inputs:
- note record
- cleaned intent and route detection result
- project rule pack YAML
- Jinja2 template file

Outputs:
- prompt_package row
- one or more prompt_step rows

For MVP, default to one prompt step unless the note clearly asks for a sequence using language like:
- first / second / third
- phase 1 / phase 2
- step one / step two
- then after that

Do not over-split. If uncertain, generate one task and include ambiguity notes.

Every prompt step must render self-contained markdown with sections:

# Task
# Source
# Cleaned Intent
# Implementation Instructions
# Guardrails
# Project Context
# Verification
# Completion Criteria
# Notes

External task key format:

`obsidian:<relative-note-path>#step-<n>`

Normalize keys so they are stable and safe for Kanban.

Do not call Kanban in this prompt.
Do not add LLM provider support.
Do not add template editing UI.

Add tests:
- one-note one-step compile
- multi-step compile for explicit sequence
- external task key stability
- guardrails from project YAML included
- verification commands from project YAML included
- ambiguity notes preserved

Output:
1. Files changed.
2. Prompt package contract.
3. Example rendered prompt.
4. Test command and result.
```

---

## Prompt 7 — Implement Kanban Client

```md
Implement the Kanban HTTP client for the companion app.

Context:
The modified Kanban app exposes tRPC endpoints under `/api/trpc` and supports:
- `projects.list`
- `projects.add`
- `workspace.getState`
- `workspace.importTasks`

A new mutation may also exist:
- `workspace.upsertTaskByExternalKey`

Implement a client that supports:

1. `list_projects()`
2. `add_project(path)`
3. `get_workspace_state(workspace_id)`
4. `import_tasks(workspace_id, payload)`
5. `upsert_task_by_external_key(workspace_id, payload)` if endpoint exists
6. capability probe that detects whether upsert is available

Delivery behavior:
- Prefer `workspace.upsertTaskByExternalKey` for one-step packages when available.
- Use `workspace.importTasks` for multi-step prompt chains and links.
- If upsert is unavailable, use `workspace.importTasks`.
- Never use direct board JSON writes.
- Never use `workspace.saveState` as the primary integration path.

Request fields for Kanban tasks:
- externalTaskKey
- title
- prompt
- startInPlanMode
- autoReviewEnabled
- autoReviewMode
- agentId
- clineSettings
- baseRef

Add tests with a fake HTTP server or mocked httpx:
- list projects
- import one task
- import linked tasks
- upsert when available
- fallback to import when upsert unavailable
- failed Kanban response creates clear error

Output:
1. Files changed.
2. Supported Kanban calls.
3. Example payloads.
4. Test command and result.
```

---

## Prompt 8 — Implement Delivery Workflow

```md
Implement delivery workflow from approved prompt package to Kanban.

Requirements:
- Add API endpoint: `POST /api/packages/{id}/deliver`
- Load package and steps from SQLite.
- Build Kanban payload.
- Create delivery record with status `dispatching`.
- Call Kanban client.
- Store request JSON and response JSON.
- Mark delivery `delivered` or `failed`.
- Mark package/steps delivered only on success.
- Expose `GET /api/deliveries` and `GET /api/deliveries/{id}`.
- Expose `POST /api/deliveries/{id}/retry`.

Manual retry only.
No auto-retry.
No exponential backoff.
No target rerouting.
No multi-target delivery registry.
No session registry.
No execution tracking.

Tests:
- successful delivery updates records
- failed delivery stores error
- retry creates a new attempt or updates according to a simple documented policy
- multi-step package uses importTasks with links
- one-step package uses upsert if available

Output:
1. Files changed.
2. Delivery status lifecycle.
3. Retry behavior.
4. Test command and result.
```

---

## Prompt 9 — Build Minimal Frontend Shell Matching Kanban Style

```md
Build the minimal frontend shell for `kanban-prompt-companion`.

Context:
- The app should visually match the modified Kanban app’s styling conventions.
- It should feel like a sibling local tool, not a separate SaaS dashboard.
- Do not copy protected branding, logos, or proprietary assets.
- Use Tailwind CSS and simple component primitives.

Screens:
- Intake
- Review
- Deliveries
- Settings

Shell requirements:
- compact top bar or side rail
- muted background
- card/panel layout
- simple status badges
- restrained accent color
- typography and spacing consistent with Kanban style guide
- responsive enough for desktop browser use

Do not implement:
- dashboard
- charts
- role switcher
- user menu
- target manager
- rules editor
- templates editor
- dictionary editor
- logs page
- metrics page

Create:
- layout component
- navigation component
- status badge component
- card/panel component if needed
- API client skeleton
- empty/loading/error states, but keep them simple

Output:
1. Files changed.
2. Screens created.
3. Styling choices and how they align with Kanban.
4. Run command and result.
```

---

## Prompt 10 — Implement Intake Page

```md
Implement the Intake page.

API:
- `GET /api/notes`
- `GET /api/notes/{id}`
- `POST /api/notes/{id}/reprocess`

UI requirements:
- list notes in a simple table or card list
- show title/path/status/detected project/discovered time/error
- search by title/path
- filter by status
- click row to show detail panel
- detail panel shows raw transcript and frontmatter summary
- reprocess button for failed or stale notes

Visual style:
- match Kanban local app style
- compact but readable
- no data grid library unless already present and lightweight
- no virtualization
- no metrics

Tests:
- renders note list
- filters by status
- opens detail
- calls reprocess

Output:
1. Files changed.
2. Intake behavior.
3. Test command and result.
```

---

## Prompt 11 — Implement Review Page

```md
Implement the Review page. This is the core frontend screen.

API:
- `GET /api/packages?status=needs_review`
- `GET /api/packages/{id}`
- `PATCH /api/packages/{id}`
- `POST /api/packages/{id}/approve`
- `POST /api/packages/{id}/reject`
- `POST /api/packages/{id}/deliver`

UI requirements:
- left list of packages needing review
- right detail/preview panel
- show source note path
- show cleaned intent
- show target workspace/harness/baseRef
- show prompt steps
- markdown preview of selected prompt step
- editable prompt body textarea or markdown editor
- approve button
- reject button
- deliver to Kanban button after approval
- show ambiguity notes prominently

Keep the UI minimal and Kanban-like.
Do not add template editor, rules editor, LLM assist, or diff viewer in MVP.

Tests:
- loads review queue
- selects package
- edits prompt body
- approves package
- rejects package
- delivers approved package
- shows error on failed delivery

Output:
1. Files changed.
2. Review behavior.
3. Test command and result.
```

---

## Prompt 12 — Implement Deliveries Page

```md
Implement the Deliveries page.

API:
- `GET /api/deliveries`
- `GET /api/deliveries/{id}`
- `POST /api/deliveries/{id}/retry`

UI requirements:
- list delivery attempts
- show package title
- status
- Kanban workspace
- method: importTasks or upsertTaskByExternalKey
- created time
- delivered time
- error message if failed
- detail drawer/panel with request/response JSON
- retry button only for failed deliveries

Do not add:
- reroute
- target registry
- target health checks
- session registry
- execution logs
- charts

Tests:
- renders deliveries
- opens detail
- retries failed delivery
- hides retry for successful delivery

Output:
1. Files changed.
2. Delivery UI behavior.
3. Test command and result.
```

---

## Prompt 13 — Implement Minimal Settings Page

```md
Implement the minimal Settings page.

Settings fields:
- vault path
- voice inbox path
- processed folder path, optional
- Kanban base URL
- default Kanban workspace ID
- rules directory path
- templates directory path

API:
- `GET /api/settings`
- `PATCH /api/settings`
- `GET /api/kanban/workspaces`

UI requirements:
- simple form
- test Kanban connection button
- workspace picker from Kanban if available
- save button
- show validation errors

Do not implement:
- secrets database
- encrypted settings
- users
- roles
- LLM provider settings
- n8n settings
- target registry settings
- advanced admin tabs

Tests:
- loads settings
- validates required fields
- saves settings
- loads Kanban workspaces

Output:
1. Files changed.
2. Settings behavior.
3. Test command and result.
```

---

## Prompt 14 — Add Optional Note Frontmatter Writeback

```md
Implement optional source note frontmatter writeback.

Config flag:
- `writeback_enabled: true|false`

When a package is delivered successfully and writeback is enabled, update the source note frontmatter with:

```yaml
prompt_companion:
  status: delivered
  package_id: <id>
  delivered_at: <iso timestamp>
  kanban_workspace_id: <workspace id>
```

Requirements:
- Preserve existing frontmatter keys.
- Preserve body content.
- Do not move files in this prompt.
- Write atomically: temp file then rename.
- If writeback fails after successful Kanban delivery, do not mark delivery failed. Record a note warning/error separately.

Tests:
- writeback preserves existing keys
- writeback adds prompt_companion block
- disabled writeback does nothing
- writeback failure does not corrupt note

Output:
1. Files changed.
2. Writeback behavior.
3. Test command and result.
```

---

## Prompt 15 — End-to-End MVP Test

```md
Create an end-to-end MVP test for the full loop.

Scenario:
Given a sample Obsidian markdown note in a temporary voice inbox:

1. watcher detects the note
2. note is stored in SQLite
3. compiler generates a prompt package
4. package appears in review API
5. test approves the package
6. test delivers the package to a fake Kanban server
7. fake Kanban server receives valid task payload
8. delivery record is marked delivered
9. optional writeback adds provenance frontmatter

Requirements:
- Use temporary directories and temporary SQLite DB.
- Use fake Kanban HTTP server or mocked httpx.
- Assert the payload includes `externalTaskKey`, `title`, `prompt`, `baseRef`, and `agentId` where configured.
- Assert no n8n, Postgres, LLM provider, dashboard, or target registry is required.

Output:
1. Test file created.
2. End-to-end behavior covered.
3. Test command and result.
```

---

## Prompt 16 — Hard Scope Audit Before First Manual Run

```md
Perform a hard scope audit of the current implementation.

Context:
This project exists to avoid repeating PromptForge’s platform expansion.

Inspect the repository and produce `docs/SCOPE_AUDIT.md`.

Check for forbidden complexity:
- Postgres dependency
- n8n dependency
- users table
- roles
- role switcher
- multi-target delivery registry
- session registry
- rules CRUD
- templates CRUD
- dictionary CRUD
- metrics dashboard
- charts
- LLM provider marketplace
- encrypted secrets database
- direct writes to Kanban JSON state
- use of `workspace.saveState` as primary integration path

For each item:
- Present: yes/no
- File paths if present
- Recommendation if present

Also verify required MVP pieces exist:
- watcher
- note parser
- SQLite state
- deterministic cleanup
- prompt compiler
- review page
- delivery workflow
- Kanban client
- failed delivery retry
- Kanban-like styling guide

Do not modify files.

Output:
1. `docs/SCOPE_AUDIT.md`
2. Summary of any scope violations.
3. Recommended fixes before first manual run.
```
