# Phase 4 Prompt — Backend API and Kanban Delivery Flow

You are exposing the minimal backend API for the Kanban Prompt Companion and wiring delivery to the modified Kanban app.

The ingest/pipeline modules and SQLite persistence should already exist.

## Goal

Expose only the API needed for:

```text
health
intake list/detail
review queue
prompt preview/edit
Kanban workspace discovery
Kanban payload preview
Kanban delivery
manual retry
```

Do not create a broad console/admin API.

## Required API Endpoints

Implement only these endpoints unless a test-proven need appears:

```text
GET  /health
GET  /api/intake
GET  /api/intake/{note_id}
GET  /api/review
GET  /api/packages/{package_id}
PATCH /api/steps/{step_id}
POST /api/packages/{package_id}/approve
GET  /api/kanban/workspaces
POST /api/packages/{package_id}/kanban/preview
POST /api/packages/{package_id}/kanban/deliver
GET  /api/deliveries
GET  /api/deliveries/{delivery_id}
POST /api/deliveries/{delivery_id}/retry
```

Do not add:

- rules endpoints
- template CRUD endpoints
- dictionary endpoints
- target CRUD endpoints
- metrics endpoints
- logs/fingerprint endpoints
- project CRUD endpoints
- role/user endpoints
- LLM provider endpoints

## Endpoint Behavior

### GET /health

Return:

```json
{
  "ok": true,
  "service": "kanban-prompt-companion"
}
```

### GET /api/intake

Return notes with status, title, relative path, discovered time, and linked package status if available.

Support only simple optional filters:

- `status`
- `limit`

### GET /api/intake/{note_id}

Return note details, transcript, cleaned intent/package summary if available.

### GET /api/review

Return prompt packages where `requires_review = true` or status is `review_ready`.

### GET /api/packages/{package_id}

Return package and steps.

### PATCH /api/steps/{step_id}

Allow editing only:

- `title`
- `prompt_markdown`
- `base_ref`
- `agent_id`
- `start_in_plan_mode`

Do not allow editing internal IDs, external task key after delivery, or dependencies unless explicitly implemented later.

### POST /api/packages/{package_id}/approve

Mark package approved/reviewed. Do not auto-deliver unless request includes explicit `deliver: true`.

### GET /api/kanban/workspaces

Use the Kanban client to call `projects.list`. Return normalized workspace/project entries.

### POST /api/packages/{package_id}/kanban/preview

Build the exact Kanban payload from stored package/steps. Return payload and warnings.

### POST /api/packages/{package_id}/kanban/deliver

Build the payload and send to Kanban using:

- `workspace.upsertTaskByExternalKey` for single-step if available/configured, or
- `workspace.importTasks` for graph/multi-step payloads

Record request JSON, response JSON, delivered/failed status, and error message.

Do not write directly to Kanban JSON files.

### Delivery Endpoints

`GET /api/deliveries`, `GET /api/deliveries/{delivery_id}`, and `POST /api/deliveries/{delivery_id}/retry` should stay narrow and delivery-focused.

Retry should rebuild from current package/steps, not blindly replay stale request JSON unless explicitly needed.

## Kanban Delivery Rules

- Use configured `KPC_KANBAN_BASE_URL`.
- Use configured workspace ID or package workspace ID.
- If workspace ID is missing, return clear error.
- If Kanban is unreachable, classify as connection error.
- If Kanban returns tRPC error, preserve code/message.
- If passcode/auth is needed, return actionable error unless the existing client supports safe verify.

## API Shape Rules

- JSON only.
- Keep responses boring and explicit.
- No hidden side effects beyond stated mutation.
- No global admin settings mutation in this phase.
- No auth unless already required by local deployment.

## Required Tests

Use FastAPI TestClient or equivalent.

Tests:

- health endpoint
- list intake returns seeded notes
- review queue returns seeded packages
- step edit updates allowed fields only
- package preview returns expected Kanban payload
- delivery success records response
- delivery failure records error
- retry rebuilds and resends current package
- workspace discovery normalizes Kanban response
- no route exists for rejected PromptForge console domains

Mock Kanban HTTP calls.

## Output Required

Return:

1. Endpoints implemented.
2. Files changed.
3. Tests added and run.
4. Example request/response for preview and deliver.
5. Confirmation that no broad admin/console endpoints were added.
