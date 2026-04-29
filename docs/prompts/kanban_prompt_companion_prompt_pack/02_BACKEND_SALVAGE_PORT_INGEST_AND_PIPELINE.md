# Phase 2 Prompt — Backend Salvage Port: Ingest and Pipeline Mechanics

You are porting only the approved backend salvage mechanics into the new Kanban Prompt Companion.

Do not implement SQLite persistence yet, except tiny temporary/in-memory structures required to run tests. Do not build frontend UI in this phase.

## Goal

Implement the backend mechanics from source note to Kanban manifest preview:

```text
markdown note
→ safe read
→ frontmatter/body/transcript extraction
→ deterministic cleanup/directives
→ PromptPackageV1 contract
→ file-based Jinja rendering
→ Kanban import manifest preview
```

## Source Repos to Inspect

Backend salvage source:

- `prompt-forge/promptforge_watcher/watcher.py`
- `prompt-forge/promptforge_watcher/writeback.py`
- `prompt-forge/promptforge_services/pipeline.py`
- `prompt-forge/promptforge_services/models.py`
- `prompt-forge/promptforge_services/kanban_manifest_builder.py`
- `prompt-forge/promptforge_services/kanban_client.py`

Use the salvage report decisions:

- copy watcher debounce queue where small and local
- adapt startup scan, watchdog event handling, content hash dedupe, eligibility checks
- rewrite safe partial-read with explicit stable size/mtime checks
- rewrite frontmatter parsing around `python-frontmatter`
- adapt section extraction
- adapt directive/parser concepts but rewrite grammar for Kanban companion
- rewrite transcript cleanup beyond old shallow `normalize_transcript()`
- adapt versioned Pydantic model into `PromptPackageV1`
- adapt Jinja rendering using file templates only
- copy/adapt Kanban manifest models and binding validation
- adapt Kanban HTTP client, stripping PromptForge imports

## Explicitly Do Not Port

Do not port:

- Postgres repository code
- schema migrations
- n8n webhook code
- LLM provider router
- delivery target registry
- tmux/session dispatch
- PromptForge delivery dispatcher
- DB-backed rulesets/templates/dictionary
- workflow error records
- processing runs

## Required Backend Modules

Implement modules equivalent to:

```text
app/ingest/paths.py
app/ingest/stable_read.py
app/ingest/dedupe.py
app/ingest/markdown.py
app/ingest/watcher.py
app/pipeline/directives.py
app/pipeline/cleanup.py
app/pipeline/render.py
app/contracts.py
app/kanban/manifest.py
app/kanban/client.py
```

## Detailed Requirements

### 1. Path Filtering

Implement `is_processable_markdown_path(path)`.

Preserve behavior from PromptForge watcher:

- accept `.md`
- reject hidden files
- reject Obsidian/temp/swap-ish files
- reject directories

Add tests for normal note accepted, hidden note rejected, temp/swap note rejected, and non-md rejected.

### 2. Stable Read

Implement safe read behavior that waits until file size and mtime are stable across at least two checks.

Requirements:

- configurable timeout
- configurable poll interval
- clear error if file never stabilizes
- read text as UTF-8

### 3. Hash Dedupe

Implement SHA-256 content hash helper. In Phase 2 this can be in-memory.

### 4. Markdown / Frontmatter Extraction

Use `python-frontmatter`.

Implement a `LoadedNote` model with:

```python
absolute_path: str
relative_path: str
title: str
frontmatter: dict
body: str
control_text: str | None
transcript_text: str
content_hash: str
```

Extraction behavior:

- frontmatter may be absent
- title should come from frontmatter title or filename stem
- transcript should come from `## Transcript` section if present
- control text should come from `## Control` section if present
- fallback transcript should be note body if no transcript section exists
- skip note if `status` is not `new` unless status absent
- skip note if `watch_eligible` is explicitly false
- reject empty transcript

### 5. Directives

Rewrite directive parsing for this app.

Support simple forms in control text or transcript:

```text
project is kanban
project: kanban
target project is kanban
workspace is kanban
workspace: kanban
harness is codex
agent is codex
base ref is main
base: main
prompt type is coding
chain: yes
```

Return:

```python
Directives(
  project_key: str | None,
  workspace_id: str | None,
  harness: str | None,
  base_ref: str | None,
  prompt_type: str | None,
  wants_chain: bool,
  warnings: list[str]
)
```

Do not support PromptForge destinations such as chat session, generic queue, obsidian note, claude session, codex session.

### 6. Cleanup

Implement deterministic cleanup for speech artifacts.

Requirements:

- remove common filler words conservatively
- normalize repeated whitespace
- remove repeated false starts where obvious
- preserve code-ish tokens, paths, flags, filenames, class names, function names
- do not over-summarize
- return both `cleaned_text` and `cleanup_notes`

### 7. PromptPackageV1 Contract

Create minimal Pydantic models:

```python
PromptPackageV1
PromptStepV1
PromptGuardrailsV1
PromptVerificationV1
```

Required package fields:

- `version = "v1"`
- `source_note_path`
- `cleaned_intent`
- `project_key`
- `workspace_id | None`
- `steps: list[PromptStepV1]`

Step fields:

- `step_index`
- `title`
- `prompt_markdown`
- `external_task_key`
- `base_ref | None`
- `agent_id | None`
- `start_in_plan_mode: bool`
- `depends_on_step_indices: list[int]`

### 8. File-Based Jinja Rendering

Implement renderer that loads `templates/prompt_package.md.j2`, renders each step, validates package before render, and optionally formats markdown only if safe.

### 9. Kanban Manifest Builder

Adapt/copy relevant logic from `kanban_manifest_builder.py`.

Build payload compatible with Kanban:

```json
{
  "version": "v1",
  "tasks": [
    {
      "externalTaskKey": "...",
      "title": "...",
      "prompt": "...",
      "baseRef": "main",
      "agentId": "codex",
      "startInPlanMode": true
    }
  ],
  "links": []
}
```

If prompt package has multiple steps, represent them as multiple tasks and links.

### 10. Kanban Client

Adapt `kanban_client.py` only enough for:

- `projects.list`
- `projects.add` if needed
- `workspace.getState`
- `workspace.importTasks`
- `workspace.upsertTaskByExternalKey` if present and configured

Requirements:

- use `httpx`
- support base URL config
- support workspace ID header/query as Kanban expects
- classify connection/auth/tRPC errors clearly
- no direct Kanban file writes

## Required Tests

Add tests for all modules listed above. Mock Kanban HTTP responses.

## Phase Output

Return:

1. Files created/changed.
2. Which salvage code was copied vs adapted vs rewritten.
3. Tests added.
4. Commands run and results.
5. Confirmation that rejected PromptForge systems were not ported.
