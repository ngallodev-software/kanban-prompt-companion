# Phase 8 Prompt — Scope Guardrail Review

You are performing a final scope guardrail review before MVP completion.

Your job is to find evidence that the new Kanban Prompt Companion has started to recreate PromptForge platform complexity.

Be strict. Be blunt.

## Review Inputs

Inspect the new project and compare it against the intended workflow:

```text
Obsidian markdown voice note
→ cleaned transcript / cleaned intent
→ generated prompt package
→ human review
→ Kanban task delivery
```

Also inspect known rejected source patterns from:

- `prompt-forge`
- `prompt-forge-console`

## Hard Rejection Checklist

Search the new project for evidence of these forbidden systems:

- Postgres dependency or schema
- n8n dependency or webhook workflow requirement
- LLM provider router
- tmux/session dispatch
- multi-target delivery registry
- delivery session registry
- DB-backed rulesets
- DB-backed prompt templates
- term dictionary UI
- dashboard/metrics/SLA charts
- logs/error fingerprint UI
- role switcher
- user/role/auth model
- project/user scope model
- large settings admin page
- pipeline visualization
- generic admin CRUD pages
- direct writes to Kanban `board.json` or `sessions.json`

For each found item, classify:

- `acceptable_mvp_exception`
- `warning`
- `must_remove_before_mvp`

## Dependency Review

List backend dependencies and classify:

- required
- optional but acceptable
- should remove
- forbidden

Expected acceptable backend dependencies:

- fastapi
- uvicorn
- pydantic
- watchdog
- python-frontmatter
- jinja2
- httpx
- pytest
- optional mdformat
- optional rapidfuzz

Expected forbidden backend dependencies:

- psycopg
- libtmux
- cryptography for DB secret management
- LLM provider SDKs
- n8n clients

List frontend dependencies and classify.

Expected acceptable frontend dependencies:

- React
- Vite
- TypeScript
- Tailwind
- React Query
- clsx/tailwind-merge
- minimal Radix primitives actually used
- optional lucide-react

Expected suspicious/avoid dependencies:

- recharts
- cmdk
- react-window
- zustand unless justified
- broad Radix package set
- react-hook-form/zod unless settings forms became complex

## API Surface Review

List all backend routes.

Expected upper bound:

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

Flag any additional route and explain whether it is justified.

## Database Review

List all tables.

Expected upper bound:

```text
notes
prompt_packages
prompt_steps
deliveries
```

Flag any additional table.

## Frontend Screen Review

List all screens/routes.

Expected upper bound:

```text
/intake
/review
/deliveries
/settings
```

Flag any additional screen.

## Kanban Integration Review

Verify:

- uses Kanban HTTP/tRPC API or CLI integration seam
- does not directly mutate Kanban JSON files
- uses stable `externalTaskKey`
- preserves Kanban as task execution system of record
- does not duplicate Kanban board/task management

## Final Report Format

Produce a markdown report:

# Scope Guardrail Review

## Summary Verdict

Choose one:

- `MVP scope is clean`
- `MVP scope has warnings but can proceed`
- `MVP scope has blockers`

## Findings

Table:

| Area | Finding | Severity | Evidence | Required action |

## Dependency Review
## API Surface Review
## Database Review
## Frontend Screen Review
## Kanban Integration Review
## Must-Fix Before MVP
## Safe to Defer
## Final Recommendation

Do not modify files in this review phase unless explicitly asked after the report.
