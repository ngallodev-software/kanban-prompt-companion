# Minimal Kanban Voice-Prompt Companion — Design Document

**Date:** 2026-04-28  
**Working name:** `kanban-prompt-companion`  
**Status:** Draft for implementation planning  
**Primary goal:** Convert Obsidian speech-to-text notes into reviewed, high-quality AI coding prompts and deliver them into the modified Kanban app as executable cards.

---

## 1. Executive Summary

This project is not a rebuild of PromptForge. It is a smaller Kanban companion service.

The system watches an Obsidian voice-note inbox, processes transcribed markdown notes, removes speech artifacts, applies a small file-based ruleset, generates one or more execution-ready prompt steps, allows human review, and delivers approved prompt steps to the modified Kanban app through its external integration API.

The system must stay narrow:

```text
Obsidian note
  → cleaned intent
  → prompt package
  → human review
  → Kanban task delivery
```

Everything else is explicitly out of scope until the first loop is reliable.

---

## 2. Design Constraints

### 2.1 Product Constraints

- Single local operator.
- Local network / homelab deployment first.
- Obsidian speech capture and Speaches transcription are already solved and are not part of this project.
- Kanban is the task system of record.
- This companion app owns prompt preparation state, not Kanban.
- The frontend should visually match the Kanban app so it feels like part of the same local toolchain, even though it is a separate app and should not copy protected branding or claim ownership of Kanban.

### 2.2 Complexity Constraints

Do not repeat PromptForge’s platform expansion. The previous PromptForge backend became a broad FastAPI/Postgres operations platform with console APIs, optional LLM providers, n8n integration, secrets infrastructure, and delivery/session abstractions. The previous frontend became a multi-page admin console with dashboards, rules/templates/dictionary CRUD, settings, logs, health, and metrics.

This implementation must avoid:

- multi-user roles/auth
- role switchers
- n8n as a required dependency
- Postgres as the default datastore
- multi-target delivery registry
- session registry
- LLM provider marketplace
- ruleset/version marketplace
- template management UI
- dictionary management UI
- metrics dashboard
- throughput/SLA charts
- generic admin console
- DB-backed settings/secrets
- direct writes to Kanban JSON state
- replacing Kanban functionality

---

## 3. Relationship to Kanban

### 3.1 Kanban Integration Surface

The modified Kanban fork already exposes useful integration primitives:

- `projects.list`
- `projects.add`
- `workspace.getState`
- `workspace.importTasks`
- CLI task import/create/update/list surfaces
- `externalTaskKey` for idempotent external identity

The companion app should use Kanban through the supported HTTP/tRPC integration path. It should not directly edit `board.json`, `sessions.json`, or any Kanban runtime state files.

### 3.2 Card Model Reality

Kanban cards currently accept a constrained set of task fields:

- `externalTaskKey`
- `title`
- `prompt`
- `startInPlanMode`
- `autoReviewEnabled`
- `autoReviewMode`
- `images`
- `agentId`
- `clineSettings`
- `baseRef`

Kanban does not currently have first-class generic metadata, comments, tags, checklists, or prompt-chain fields. Therefore, the companion app must keep its internal structured state in its own SQLite database and deliver only executable task payloads to Kanban.

### 3.3 Expected Kanban Addition

The recommended Kanban-side enhancement is:

```text
workspace.upsertTaskByExternalKey
```

The new companion can initially use `workspace.importTasks`, but `workspace.upsertTaskByExternalKey` is preferred once available because prompt revision is a normal part of the review loop.

---

## 4. Target Architecture

```text
Obsidian Vault
  /voice/inbox/*.md
        │
        ▼
Note Watcher
  - detects stable markdown files
  - hashes content
  - avoids duplicate processing
        │
        ▼
SQLite State Store
  - notes
  - prompt_packages
  - prompt_steps
  - deliveries
        │
        ▼
Prompt Compiler
  - parse frontmatter/body
  - remove speech artifacts
  - detect project/routing hints
  - apply file-based rules
  - render Jinja2 prompt template
        │
        ▼
Review UI
  - intake list
  - prompt preview/edit
  - rule match summary
  - approve/send
        │
        ▼
Kanban Client
  - projects.list/projects.add
  - workspace.importTasks or workspace.upsertTaskByExternalKey
  - workspace.getState
        │
        ▼
Kanban Board
  - cards in backlog
  - prompt text ready for Cline/Codex/Claude harness
```

---

## 5. Backend Design

### 5.1 Backend Shape

Recommended implementation:

```text
Python 3.11+
FastAPI
SQLite
watchdog
python-frontmatter
PyYAML
Jinja2
httpx
```

The backend should be a single service with an embedded watcher task. A split API service + watcher process is acceptable later, but not required for MVP.

### 5.2 Backend Responsibilities

The backend owns:

- watching the Obsidian voice inbox
- parsing markdown/frontmatter
- deduplicating by content hash
- storing source note records
- compiling prompt packages
- storing prompt package and prompt step records
- exposing a minimal review API
- delivering approved prompt steps to Kanban
- recording delivery requests/responses/errors
- updating source note frontmatter with minimal provenance, if enabled

The backend does not own:

- speech capture
- speech-to-text transcription
- Kanban board state
- coding-agent execution
- AI CLI session lifecycle
- multi-target delivery
- user management
- LLM provider routing
- dashboard metrics

---

## 6. Frontend Design

### 6.1 Frontend Shape

Recommended implementation:

```text
React
Vite
TypeScript
Tailwind CSS
Radix/shadcn-style primitives where useful
Lucide icons
```

The UI should look like a sibling of Kanban. It should borrow the visual grammar from the Kanban app’s frontend conventions:

- Tailwind-first styling
- compact local-app layout
- card-based surfaces
- muted borders
- simple status badges
- clean typography
- restrained accent color usage
- no marketing-style UI
- no enterprise admin-console chrome

The app should not copy Kanban logos, names, protected branding, or proprietary assets. The goal is stylistic continuity for a local toolchain, not impersonation.

### 6.2 Screens

#### 1. Intake

Purpose: Show source notes discovered from Obsidian.

Required elements:

- note title/path
- status
- detected project/routing hint
- discovered time
- content hash or short provenance ID
- processing error if present
- action: open detail / reprocess

Avoid:

- dashboards
- complex metrics
- nested lineage graphs
- advanced filtering beyond simple status/search

#### 2. Review

Purpose: Review generated prompt packages before delivery.

Required elements:

- source note summary
- cleaned intent
- generated prompt preview
- prompt step list if the package has multiple steps
- target Kanban workspace
- target harness hint
- guardrails
- verification commands
- edit prompt body
- approve/send to Kanban
- reject/hold

This is the core screen.

#### 3. Deliveries

Purpose: Show delivery status and retry failures.

Required elements:

- package title
- Kanban workspace
- action used: `importTasks` or `upsertTaskByExternalKey`
- response status
- created/updated task IDs if available
- error message
- retry button

Avoid:

- multi-target reroute UI
- session registry UI
- delivery target CRUD

#### 4. Settings

Purpose: Minimal local configuration.

Required fields:

- Obsidian vault path
- voice inbox relative path
- processed folder relative path, optional
- Kanban base URL
- default Kanban workspace ID
- rules directory path
- templates directory path

Avoid:

- encrypted secret database
- user settings
- role settings
- LLM provider management
- target registry management

### 6.3 Navigation

A minimal left rail or top bar is enough:

```text
Intake | Review | Deliveries | Settings
```

No dashboard route in MVP.

---

## 7. Data Model

Use SQLite. Frontmatter remains source/provenance, not the primary state database.

### 7.1 `notes`

```sql
CREATE TABLE notes (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  relative_path TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  title TEXT,
  raw_markdown TEXT NOT NULL,
  raw_transcript TEXT,
  frontmatter_json TEXT,
  status TEXT NOT NULL,
  detected_project_key TEXT,
  discovered_at TEXT NOT NULL,
  processed_at TEXT,
  error TEXT
);
```

Status values:

```text
new
processing
compiled
needs_review
rejected
delivered
error
archived
```

### 7.2 `prompt_packages`

```sql
CREATE TABLE prompt_packages (
  id TEXT PRIMARY KEY,
  note_id TEXT NOT NULL REFERENCES notes(id),
  title TEXT NOT NULL,
  cleaned_intent TEXT NOT NULL,
  summary TEXT,
  target_project_key TEXT,
  target_workspace_id TEXT,
  target_repository_path TEXT,
  target_harness TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  error TEXT
);
```

Status values:

```text
draft
needs_review
approved
delivering
delivered
failed
rejected
```

### 7.3 `prompt_steps`

```sql
CREATE TABLE prompt_steps (
  id TEXT PRIMARY KEY,
  package_id TEXT NOT NULL REFERENCES prompt_packages(id),
  step_index INTEGER NOT NULL,
  external_task_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  prompt_markdown TEXT NOT NULL,
  base_ref TEXT,
  target_harness TEXT,
  start_in_plan_mode INTEGER NOT NULL DEFAULT 1,
  auto_review_enabled INTEGER NOT NULL DEFAULT 0,
  auto_review_mode TEXT,
  depends_on_step_ids_json TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

Status values:

```text
draft
approved
delivered
failed
```

### 7.4 `deliveries`

```sql
CREATE TABLE deliveries (
  id TEXT PRIMARY KEY,
  package_id TEXT NOT NULL REFERENCES prompt_packages(id),
  kanban_workspace_id TEXT NOT NULL,
  kanban_base_url TEXT NOT NULL,
  method TEXT NOT NULL,
  request_json TEXT NOT NULL,
  response_json TEXT,
  status TEXT NOT NULL,
  error TEXT,
  created_at TEXT NOT NULL,
  delivered_at TEXT
);
```

Status values:

```text
queued
dispatching
delivered
failed
```

---

## 8. File-Based Configuration

### 8.1 App Config

Use `.env` and one YAML config file.

Example `.env`:

```bash
KPC_HOST=127.0.0.1
KPC_PORT=8091
KPC_DB_PATH=/lump/apps/kanban-prompt-companion/data/app.sqlite
KPC_VAULT_PATH=/lump/obsidian/vault
KPC_VOICE_INBOX=voice/inbox
KPC_PROCESSED_FOLDER=voice/processed
KPC_KANBAN_BASE_URL=http://127.0.0.1:3484
KPC_DEFAULT_WORKSPACE_ID=kanban
KPC_RULES_DIR=/lump/apps/kanban-prompt-companion/rules
KPC_TEMPLATES_DIR=/lump/apps/kanban-prompt-companion/templates
```

### 8.2 Project Rule Pack

Example `rules/projects/kanban.yaml`:

```yaml
projectKey: kanban
workspaceId: kanban
repositoryPath: /lump/apps/kanban
defaultBaseRef: main
defaultHarness: codex
defaultStartInPlanMode: true

markers:
  - kanban
  - board
  - card
  - task
  - cline
  - prompt chain

speechCleanup:
  removeFillers: true
  normalizeWhitespace: true
  preserveCodeTerms: true

promptDefaults:
  guardrails:
    - Do not modify unrelated files.
    - Keep the implementation minimal.
    - Preserve existing behavior unless explicitly requested.
    - Add or update targeted tests for behavior changes.
  verification:
    - npm run test:fast
    - npm run build

delivery:
  mode: review_first
  chainAsLinkedTasks: true
```

---

## 9. Prompt Compiler

### 9.1 Input Sources

The compiler reads:

- note frontmatter
- note body
- configured project rule packs
- prompt templates

Preferred explicit note directives:

```yaml
project: kanban
type: coding
harness: codex
base_ref: main
```

Inline speech-friendly directives should also work:

```text
project is kanban, prompt type is coding cli, target harness is codex
```

### 9.2 Processing Steps

```text
1. Read stable markdown file.
2. Parse frontmatter and body.
3. Extract raw transcript.
4. Remove speech artifacts.
5. Detect project/routing hints.
6. Build cleaned intent.
7. Decide whether one task or multiple linked steps are needed.
8. Render prompt markdown using file template.
9. Store package and steps.
10. Mark package as needs_review.
```

### 9.3 Prompt Output Contract

Every Kanban-delivered prompt should be self-contained:

```md
# Task

<one clear implementation objective>

# Source

- Obsidian note: `<relative path>`
- Prompt package: `<package id>`
- Step: `<n of m>`

# Cleaned Intent

<cleaned user intent>

# Implementation Instructions

<concrete coding instructions>

# Guardrails

- Do not modify unrelated files.
- Do not broaden scope.
- Preserve existing behavior unless explicitly changed.
- Add or update tests for behavior changes.

# Project Context

<repo path and relevant notes from rule pack>

# Verification

Run:

```bash
<commands>
```

# Completion Criteria

- <criterion 1>
- <criterion 2>
- <criterion 3>

# Notes

<any ambiguity or human decision>
```

---

## 10. Kanban Delivery Contract

### 10.1 Initial Contract: `workspace.importTasks`

```json
{
  "version": "v1",
  "tasks": [
    {
      "externalTaskKey": "obsidian:voice/inbox/2026-04-28-note.md#step-1",
      "title": "Implement minimal note watcher",
      "prompt": "# Task\n\nImplement...",
      "startInPlanMode": true,
      "autoReviewEnabled": false,
      "agentId": "codex",
      "baseRef": "main"
    }
  ],
  "links": [],
  "startTaskExternalKeys": []
}
```

### 10.2 Preferred Contract: `workspace.upsertTaskByExternalKey`

Once available:

```json
{
  "externalTaskKey": "obsidian:voice/inbox/2026-04-28-note.md#step-1",
  "title": "Implement minimal note watcher",
  "prompt": "# Task\n\nImplement...",
  "baseRef": "main",
  "startInPlanMode": true,
  "autoReviewEnabled": false,
  "agentId": "codex",
  "updatePolicy": "replace_editable_fields"
}
```

### 10.3 Prompt Chains

Prompt chains should be represented as multiple Kanban tasks plus links, not as one large task.

---

## 11. Minimal API

### 11.1 Health

```text
GET /health
```

Response:

```json
{
  "ok": true,
  "db": "ok",
  "vault": "ok",
  "kanban": "unknown"
}
```

### 11.2 Intake

```text
GET /api/notes
GET /api/notes/{id}
POST /api/notes/{id}/reprocess
```

### 11.3 Review

```text
GET /api/packages?status=needs_review
GET /api/packages/{id}
PATCH /api/packages/{id}
POST /api/packages/{id}/approve
POST /api/packages/{id}/reject
```

### 11.4 Delivery

```text
POST /api/packages/{id}/deliver
GET /api/deliveries
GET /api/deliveries/{id}
POST /api/deliveries/{id}/retry
```

### 11.5 Settings

```text
GET /api/settings
PATCH /api/settings
GET /api/kanban/workspaces
```

Keep this list short. Adding endpoints requires a written reason tied to the core loop.

---

## 12. Note Lifecycle

Recommended MVP behavior:

1. New note is detected in `voice/inbox`.
2. System waits until the file is stable.
3. System records a note row.
4. System compiles a prompt package.
5. User reviews and sends to Kanban.
6. System records delivery result.
7. System optionally updates source note frontmatter:

```yaml
prompt_companion:
  status: delivered
  package_id: pkg_123
  delivered_at: 2026-04-28T21:00:00Z
  kanban_workspace_id: kanban
```

Move/archive behavior should be optional and should not be required for the first implementation.

---

## 13. Testing Strategy

### 13.1 Unit Tests

- markdown/frontmatter parsing
- speech cleanup
- directive extraction
- project detection
- Jinja2 rendering
- external task key generation
- Kanban payload generation

### 13.2 Integration Tests

- note file → SQLite note row
- note row → prompt package
- prompt package → Kanban import payload
- failed Kanban call → failed delivery record
- retry delivery → new delivery attempt

### 13.3 End-to-End Test

Given one sample note in a test vault:

1. watcher detects note
2. package is generated
3. package appears in review queue
4. test approves package
5. app sends payload to fake Kanban server
6. delivery status becomes delivered
7. note provenance is updated if writeback is enabled

---

## 14. Implementation Phases

### Phase 0 — Repository and Style Inventory

- Create new sibling app directory.
- Inspect Kanban UI styling conventions.
- Extract theme tokens/classes to mimic, not copy branding.
- Confirm Kanban runtime URL and workspace ID.

### Phase 1 — Backend Core Loop

- FastAPI skeleton.
- SQLite schema.
- watcher with debounce/hash.
- note parser.
- speech cleanup.
- prompt package generation.
- minimal review API.

### Phase 2 — Kanban Delivery

- Kanban client.
- `projects.list` and `workspace.getState` probe.
- `workspace.importTasks` delivery.
- support `workspace.upsertTaskByExternalKey` when available.
- delivery records and retry.

### Phase 3 — Minimal Frontend

- Kanban-matched shell.
- Intake page.
- Review page.
- Deliveries page.
- Settings page.

### Phase 4 — Hardening

- better error handling
- writeback option
- sample rule packs
- sample templates
- documented install flow
- backup notes

---

## 15. Non-Goals

This project does not:

- replace Kanban
- run coding agents
- manage users
- manage roles
- manage arbitrary delivery targets
- require n8n
- require Postgres
- provide dashboards or analytics
- manage template versions in a database
- manage rule versions in a database
- store secrets in a database
- provide an LLM provider marketplace
- write directly to Kanban state files
- attempt to be a generic prompt platform

---

## 16. Acceptance Criteria for MVP

MVP is complete when:

1. A markdown note in the Obsidian voice inbox is detected.
2. The note is parsed and cleaned.
3. A prompt package is generated.
4. The package appears in a minimal review UI that visually matches Kanban’s local app style.
5. The user can approve delivery.
6. The app sends one or more tasks to Kanban through the supported API.
7. Delivery success/failure is recorded.
8. A failed delivery can be retried.
9. No n8n, Postgres, metrics dashboard, role management, or multi-target registry is required.
