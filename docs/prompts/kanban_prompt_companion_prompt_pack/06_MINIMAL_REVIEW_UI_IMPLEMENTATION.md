# Phase 6 Prompt — Minimal Review UI Implementation

You are implementing the minimal frontend for the Kanban Prompt Companion.

The backend API should already expose intake, review, package detail, step edit, Kanban preview, delivery, and delivery list endpoints. The style foundation should already match the modified Kanban app.

## Goal

Build only the UI needed for:

```text
see intake notes
review/edit prompt package
preview Kanban payload
deliver to Kanban
see delivery status / retry failures
```

Do not build an admin console.

## Required Screens

Implement only these screens/routes:

```text
/intake
/review
/deliveries
/settings
```

A single-page tabbed layout is acceptable if simpler.

## Screen Requirements

### /intake

Show:

- note title
- relative path
- status
- discovered/last seen time
- package status if available
- error message if failed

Actions:

- open related review package if generated
- refresh

Do not add advanced filters beyond status if already easy.

### /review

This is the core screen.

Show:

- list of review-ready prompt packages
- selected package detail
- source note path
- cleaned intent
- prompt steps
- editable title/prompt markdown/base ref/agent/start-in-plan-mode
- safe markdown preview
- Kanban payload preview
- deliver button
- delivery result

Actions:

- edit step
- save step
- approve package
- preview Kanban payload
- deliver to Kanban
- copy prompt markdown

Do not add:

- clone
- priority
- force review
- reroute
- lineage graph
- pipeline trace
- role-based permission guard

### /deliveries

Show:

- delivery status
- package/source note
- workspace ID
- created/delivered time
- error message

Actions:

- view request/response JSON in a compact details panel
- retry failed delivery

Do not add metrics, charts, SLA, dashboards, or fingerprint grouping.

### /settings

Keep this tiny.

Show/edit only local browser/backend config if currently supported:

- Kanban base URL
- Kanban workspace ID
- vault/watch folder display

If settings are environment-only, show read-only config and instructions to edit `.env`.

Do not build PromptForge-style tabbed runtime/secret/admin settings.

## API Client Requirements

Use a tiny client:

```text
GET /api/intake
GET /api/review
GET /api/packages/{id}
PATCH /api/steps/{id}
POST /api/packages/{id}/approve
GET /api/kanban/workspaces
POST /api/packages/{id}/kanban/preview
POST /api/packages/{id}/kanban/deliver
GET /api/deliveries
GET /api/deliveries/{id}
POST /api/deliveries/{id}/retry
```

Use React Query if already included.

Avoid global stores unless there is a concrete need.

## UI Style Requirements

- match Kanban visual density
- use Kanban-like cards/panels
- use compact status badges
- keep typography readable
- no marketing dashboard
- no enterprise admin portal feel

## State Handling

For edited prompt text:

- local component state is fine
- save explicitly via API
- do not use optimistic updates unless simple
- show clear unsaved state

For delivery:

- disable deliver button while delivering
- show success/failure inline
- preserve error messages from backend

## Tests Required

Add frontend tests for:

- intake list renders notes
- review screen renders package and step
- editing prompt step calls PATCH
- preview calls preview endpoint and displays payload
- deliver calls deliver endpoint and displays result
- delivery failure displays retry action
- markdown preview does not render unsafe HTML

Use mocked API responses.

## Output Required

Return:

1. Screens implemented.
2. Components added.
3. API functions added.
4. Tests added and run.
5. Dependencies added.
6. Confirmation that rejected admin-console features were not added.
