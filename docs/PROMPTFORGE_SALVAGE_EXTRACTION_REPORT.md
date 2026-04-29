# PromptForge Salvage Extraction Report

## Backend Salvage Decisions

### Speech Cleanup / Deterministic Preprocessing

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| Directive parser | `prompt-forge/promptforge_services/pipeline.py` | `adapt_minimally` | Useful, but grammar is too narrow: only "`key is value`". Keep alias idea, rewrite parser for Kanban companion directives. |
| Alias maps | `pipeline.py` | `rewrite_from_concept` | Current aliases include PromptForge destinations and CLI/chat routing. Keep concept only. |
| `normalize_transcript()` | `pipeline.py` | `rewrite_from_concept` | Too shallow. Removes only leading filler and collapses whitespace. Good seed, not enough for voice-note cleanup. |
| Project fuzzy match | `pipeline.py` | `adapt_minimally` | Useful if companion supports known project/workspace aliases. Avoid PromptForge hardcoded project list. |
| Pydantic contract shape | `models.py` | `adapt_minimally` | `AgentTaskV1` pattern is useful. Rewrite to minimal `PromptPackageV1`. |
| Render/validate pipeline | `pipeline.py` | `rewrite_from_concept` | Flow is right: preprocess -> validate -> render. Current destinations/modes are platform baggage. |
| LLM provider health/router | `pipeline.py`, `llm/*` | `reject` | Not in target workflow. No provider routing. |

### Watcher Stability Logic

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| Startup catch-up scan | `promptforge_watcher/watcher.py` | `adapt_minimally` | Correct behavior: scan existing markdown at boot. Keep local-only. |
| Watchdog event handler | `watcher.py` | `adapt_minimally` | Good create/modify/move handling. Keep without DB/import bundle coupling. |
| Per-file debounce queue | `watcher.py` | `copy_directly` | Small, useful, local robustness pattern. |
| Content hash dedupe | `watcher.py` | `adapt_minimally` | Useful. Persist hash metadata or local SQLite later; in-memory is fine for MVP but reprocesses after restart. |
| Processable markdown filter | `watcher.py` | `copy_directly` | Good hidden/temp/swap-file rejection. |
| Eligibility checks | `watcher.py` | `adapt_minimally` | Keep `status == new`, `watch_eligible != false`, non-empty transcript. Drop PromptForge route assumptions. |
| Safe partial-read retry | `watcher.py` | `rewrite_from_concept` | Existing code debounces but does not verify stable size/mtime across reads. Add explicit stable-read loop. |
| DB error recording | `watcher.py` | `reject` | Postgres coupling. Use local log/record on companion DB/file. |

### Markdown / Frontmatter Parsing

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| `_split_frontmatter()` | `watcher.py` | `rewrite_from_concept` | Works for simple YAML but target should use `python-frontmatter` as prompt requests. |
| `_extract_sections()` | `watcher.py` | `adapt_minimally` | Useful `## Control` / `## Transcript` extraction plus fallback. Keep but simplify names and errors. |
| `load_note()` | `watcher.py` | `adapt_minimally` | Good note model assembly: frontmatter, body, transcript, hash, relative path. Remove route metadata and DB assumptions. |
| Frontmatter writeback | `writeback.py` | `rewrite_from_concept` | Timestamp, unique archive path, metadata preservation useful. Current lifecycle/status/tags too PromptForge-specific. |
| Processed/error folders | `writeback.py`, `watcher.py` | `adapt_minimally` | Optional archive later. Do not make it central in MVP. |

### Prompt Rendering / Templates

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| Jinja rendering | `pipeline.py` | `adapt_minimally` | Keep `jinja2`, but load templates from files. |
| Inline `CODING_CLI_TEMPLATE` | `pipeline.py` | `rewrite_from_concept` | Useful section idea, but target needs prompt package for Kanban tasks, not CLI sessions. |
| `mdformat` normalization | `pipeline.py` | `adapt_minimally` | Useful polish if optional. Must not mutate code blocks unexpectedly. |
| DB-backed template versioning | docs/API/schema | `reject` | Not MVP. File templates only. |
| Default prompt sections | `pipeline.py`, planning docs | `rewrite_from_concept` | Keep “Project / Target / Mode / Task” idea only if useful. New output should be reviewable prompt package. |

### Kanban Manifest / Delivery

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| Manifest Pydantic models | `kanban_manifest_builder.py` | `copy_directly` | Small, exactly relevant to Kanban import contract. |
| `derive_external_task_key()` | `kanban_manifest_builder.py` | `adapt_minimally` | Keep stable key rule, change prefix/source boundary for companion. |
| Binding validation | `kanban_manifest_builder.py` | `copy_directly` | Fail-fast base URL/workspace checks are right. |
| Single-task manifest build | `kanban_manifest_builder.py` | `adapt_minimally` | Good MVP. Add title and companion metadata if Kanban supports it. |
| Kanban HTTP client | `kanban_client.py` | `adapt_minimally` | Keep tRPC paths, passcode verify, loopback fallback, typed errors. Remove PromptForge model imports. |
| Workspace discovery | `kanban_client.py` | `copy_directly` | Useful and scoped. |
| Multi-target delivery dispatch | `delivery_dispatch.py`, watcher delivery code | `reject` | Target only sends Kanban payloads. |
| tmux/session dispatch | delivery modules/tests | `reject` | Explicitly out of scope. |
| n8n/webhook delivery | `webhook.py`, docker/docs | `reject` | Explicitly out of scope. |

## Frontend Salvage Decisions

### Minimal UI Components

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| `Button` | `src/components/ui/button.tsx` | `adapt_minimally` | Small shadcn component. Keep if Radix Slot is already acceptable. |
| `Input`, `Textarea`, `Badge`, `Card`, `Table` | `src/components/ui/*` | `copy_directly` | Simple, low coupling. Restyle to Kanban companion theme. |
| `Select`, `Dialog`, `Tabs` | `src/components/ui/*` | `adapt_minimally` | Useful but bring Radix deps. Keep only if actually used. |
| Toast hook/components | `src/components/ui/toast.tsx`, `use-toast.ts` | `adapt_minimally` | Useful mutation feedback. Could replace with simpler local toaster. |
| `StatusBadge` | `src/components/pf/StatusBadge.tsx` | `rewrite_from_concept` | Good idea, but class tokens do not match current CSS vars. |
| `EmptyState`, `ErrorState`, `LoadingState` | `src/components/pf/*` | `adapt_minimally` | Useful generic states. Remove PromptForge styling assumptions. |
| Shell/nav/role components | `src/components/shell/*` | `reject` | Admin console baggage. |

### Prompt Preview / Markdown Rendering

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| `MarkdownPreview` | `src/components/pf/MarkdownPreview.tsx` | `adapt_minimally` | Small and useful, but current `dangerouslySetInnerHTML` comment is wrong for user input. Keep escaping, harden inline replacements or use sanitizer. |
| Prompt drawer layout | `src/pages/Prompts.tsx` | `rewrite_from_concept` | Useful preview/edit/action flow. Current page is ledger/admin UI. |
| Copy-to-clipboard patterns | scattered prompt UI | `rewrite_from_concept` | Add simple copy button in target. Do not port whole page. |
| Review queue page | `src/pages/Review.tsx` | `reject` | Too tied to failed runs/deliveries/pipeline triage. Target needs one review screen. |

### Kanban Preview / Apply UI

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| Preview/apply action flow | `src/pages/Prompts.tsx` | `adapt_minimally` | Good button/toast/result pattern. Strip force-review, clone, priority, lineage tabs. |
| Manifest/result display | `src/pages/Prompts.tsx` | `adapt_minimally` | Useful, but replace generic `JsonViewer` with concise payload preview. |
| Workspace selector | `src/components/pf/KanbanIntegrationPanel.tsx` | `adapt_minimally` | Useful form shape. Current classes contain broken arbitrary tokens like `border-[border]`; restyle. |
| `useKanbanWorkspaceDiscovery()` | `src/lib/kanban-discovery.ts` | `rewrite_from_concept` | Current fetches `${baseUrl}/workspaces`, while backend client uses `/api/trpc/projects.list`. Keep debounce/query idea only. |

### API Client Patterns

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| `fetchJson()` / `postJson()` | `src/services/promptforge/api.ts` | `adapt_minimally` | Useful minimal wrapper. Extract only ~40 lines. |
| `ApiError` classes | `src/services/promptforge/errors.ts` | `copy_directly` | Small and useful. |
| Kanban error humanizer | `api.ts` | `adapt_minimally` | Useful local-Docker guidance. Remove PromptForge wording. |
| Query keys | `api.ts`, `kanban-discovery.ts` | `rewrite_from_concept` | Keep small `qk` object only. |
| Full service layer/mock hydration | `api.ts`, `mock-data.ts` | `reject` | Huge admin-domain baggage. |

### Styling Patterns

| Candidate | Source | Decision | Reason |
|---|---|---:|---|
| Kanban-aligned CSS variables | `src/index.css` | `adapt_minimally` | Useful surface/text/status palette. Verify against modified Kanban app. |
| Tailwind token extension | `tailwind.config.ts` | `adapt_minimally` | Keep colors/font/radius/animations. Drop legacy shadcn compat unless components need it. |
| `App.css` | `src/App.css` | `reject` | Vite starter leftovers. |
| Dashboard/card/table admin styling | pages/components | `reject` | Does not support minimal companion loop. |

## Reuse Decision Table

| Area | Source file(s) | Candidate | Decision | Reason | Dependencies brought along | New target file/module |
|---|---|---|---:|---|---|---|
| Watcher debounce | `promptforge_watcher/watcher.py` | pending path deadline queue | `copy_directly` | small robust local pattern | `watchdog` | `app/ingest/watcher.py` |
| Startup scan | `watcher.py` | `rglob("*.md")` catch-up | `adapt_minimally` | process notes created while app offline | `pathlib` | `app/ingest/watcher.py` |
| Markdown eligibility | `watcher.py` | temp/hidden file filtering | `copy_directly` | avoids Obsidian partial/temp files | none | `app/ingest/paths.py` |
| Hash dedupe | `watcher.py` | SHA-256 note hash | `adapt_minimally` | prevents duplicate processing | `hashlib` | `app/ingest/dedupe.py` |
| Stable read | `watcher.py` | debounce only | `rewrite_from_concept` | add size/mtime stable check | none | `app/ingest/stable_read.py` |
| Frontmatter parse | `watcher.py` | `_split_frontmatter` | `rewrite_from_concept` | use `python-frontmatter` | `python-frontmatter` | `app/ingest/markdown.py` |
| Section extract | `watcher.py` | `_extract_sections` | `adapt_minimally` | control/transcript split useful | `re` | `app/ingest/markdown.py` |
| Directive parser | `pipeline.py` | `parse_directives` | `adapt_minimally` | keep aliases/warnings, change grammar | `pydantic` | `app/pipeline/directives.py` |
| Transcript cleanup | `pipeline.py` | `normalize_transcript` | `rewrite_from_concept` | too weak for voice artifacts | `regex` optional | `app/pipeline/cleanup.py` |
| Prompt contract | `models.py` | `AgentTaskV1` | `adapt_minimally` | versioned Pydantic shape useful | `pydantic` | `app/contracts.py` |
| Prompt render | `pipeline.py` | Jinja render | `adapt_minimally` | file templates only | `jinja2`, optional `mdformat` | `app/pipeline/render.py` |
| Kanban manifest | `kanban_manifest_builder.py` | manifest models/build | `copy_directly` | matches target delivery | `pydantic` | `app/kanban/manifest.py` |
| Kanban client | `kanban_client.py` | import/discovery client | `adapt_minimally` | useful tRPC/passcode/loopback logic | `httpx` | `app/kanban/client.py` |
| UI primitives | `src/components/ui/*` | Button/Input/Textarea/Card/Badge/Table | `adapt_minimally` | low coupling | React, Tailwind, maybe Radix Slot | `web/src/components/ui/*` |
| Markdown preview | `MarkdownPreview.tsx` | markdown renderer | `adapt_minimally` | useful preview, needs sanitization hardening | none or sanitizer | `web/src/components/PromptPreview.tsx` |
| Kanban UI | `Prompts.tsx`, `KanbanIntegrationPanel.tsx` | preview/apply/workspace patterns | `adapt_minimally` | flow useful, page not reusable | React Query | `web/src/features/review/*` |
| API errors | `errors.ts` | typed error classes | `copy_directly` | small and reusable | none | `web/src/api/errors.ts` |
| API wrapper | `api.ts` | `fetchJson`, `postJson` | `adapt_minimally` | extract minimal wrapper only | none | `web/src/api/client.ts` |
| Admin pages | `Rules.tsx`, `Templates.tsx`, `Targets.tsx`, `Dashboard.tsx`, `Logs.tsx`, `Pipeline.tsx`, `Settings.tsx` | console surfaces | `reject` | platform/admin scope | many | none |

## Minimal Port Plan

1. Create new project skeleton.
| Source | Target | Preserve | Drop | Tests |
|---|---|---|---|---|
| none, inspect current target docs | `kanban-prompt-companion/app`, `web`, `tests` | Python backend + minimal React UI boundary | PromptForge repo structure, console domains | app imports, health endpoint, empty UI render |

2. Port watcher debounce/hash logic.
| Source | Target | Preserve | Drop | Tests |
|---|---|---|---|---|
| `promptforge_watcher/watcher.py` | `app/ingest/watcher.py`, `app/ingest/paths.py`, `app/ingest/dedupe.py` | startup scan, watchdog create/modify/move, debounce, temp-file filter, hash dedupe | repository import, Postgres error records, webhook, LLM, delivery dispatch | startup catches existing note; temp files ignored; rapid writes process once; unchanged hash skipped |

3. Port markdown/frontmatter extraction.
| Source | Target | Preserve | Drop | Tests |
|---|---|---|---|---|
| `watcher.py`, `writeback.py` | `app/ingest/markdown.py` | relative path, title, frontmatter, body, control/transcript sections, conservative status checks | route metadata, processed-folder writeback as required path | parses YAML; missing frontmatter allowed; malformed frontmatter errors cleanly; transcript fallback works; `status != new` skipped |

4. Port deterministic cleanup.
| Source | Target | Preserve | Drop | Tests |
|---|---|---|---|---|
| `pipeline.py`, `models.py` | `app/pipeline/cleanup.py`, `app/pipeline/directives.py`, `app/contracts.py` | alias maps, parse warnings, whitespace normalization, versioned contract | CLI/chat/queue destinations, hardcoded PromptForge projects, LLM router | filler cleanup; whitespace normalization; directive extraction; unknown directive warning; empty prompt rejected |

5. Port file-based prompt rendering.
| Source | Target | Preserve | Drop | Tests |
|---|---|---|---|---|
| `pipeline.py` | `app/pipeline/render.py`, `templates/*.j2` | Jinja render, optional markdown normalization, validate-before-render | inline templates, DB template versioning, template CRUD | renders expected sections; missing required fields fail; code fences preserved; template file missing errors clearly |

6. Port minimal Kanban client/manifest builder.
| Source | Target | Preserve | Drop | Tests |
|---|---|---|---|---|
| `kanban_manifest_builder.py`, `kanban_client.py` | `app/kanban/manifest.py`, `app/kanban/client.py` | binding validation, `workspace.importTasks`, `projects.list`, passcode verify, loopback fallback, typed errors | PromptForge console record types, delivery target registry, n8n/tmux dispatch | missing binding preflight; manifest shape; tRPC unwrap; 401 passcode retry; connect timeout classified; workspace list normalized |

7. Port or rewrite minimal prompt preview UI.
| Source | Target | Preserve | Drop | Tests |
|---|---|---|---|---|
| `MarkdownPreview.tsx`, `Prompts.tsx`, `KanbanIntegrationPanel.tsx`, `errors.ts`, `api.ts` | `web/src/features/review/ReviewScreen.tsx`, `web/src/api/*` | one prompt preview/edit/deliver screen, preview payload, apply action, workspace selector, success/error display | PromptForge ledger, force review, clone, priority, lineage, permission guard, shell/sidebar | renders prompt; edit updates preview; preview errors shown; apply success shown; workspace discovery select updates binding |

8. Add tests around each ported behavior.
| Source | Target | Preserve | Drop | Tests |
|---|---|---|---|---|
| PromptForge tests as reference | `tests/`, `web/src/**/*.test.tsx` | behavior assertions, small fixtures | DB integration tests, admin console tests | watcher, parser, cleanup, render, manifest, client, UI review/deliver flow |

## Explicitly Rejected PromptForge Features

| Feature | Source files | Why rejected | Minimal alternative |
|---|---|---|---|
| Postgres schema | `docs/planning/promptforge_postgres_schema.sql`, `schema_migrations.py`, `repository.py` | Too complex; target is minimalist local companion | Local files or small SQLite state only if needed |
| n8n integration | `docker-compose.yml`, `promptforge_watcher/webhook.py`, `docs/planning/n8n_workflows/*` | Explicitly out of scope; no workflow sidecar | Direct Python processing |
| LLM provider router | `promptforge_services/llm/*`, `watcher.py` | Target flow deterministic + human review | Optional manual enhancement later, not in MVP |
| Multi-target delivery registry | `delivery_dispatch.py`, `delivery.py`, delivery target API/types | Target sends only Kanban payloads | Single Kanban client |
| Delivery session registry | migration/docs/tests around session registry and tmux | Live sessions are not target workflow | Store Kanban response/error |
| DB-backed rulesets | schema/API/`Rules.tsx`/types | Rule engine/platform feature | Small deterministic cleanup functions |
| DB-backed prompt templates | schema/API/`Templates.tsx` | Template CRUD/versioning overbuilt | File-based Jinja templates |
| Term dictionary UI | `Dictionary.tsx`, dictionary API/types | Admin feature, not MVP | Hardcoded/local alias config if needed |
| Dashboard/metrics | `Dashboard.tsx`, metrics APIs | Operational console sprawl | Simple counts on review screen if needed |
| Logs/error fingerprint UI | `Logs.tsx`, error fingerprint API | Admin observability sprawl | Inline error display + local logs |
| Role switcher | `RoleSwitcher.tsx`, permission guards | Single-user local app | No roles |
| Project/user scope model | settings/schema/API/types | Multi-tenant/platform model | One local config with optional workspace/project label |
| Large settings admin page | `Settings.tsx`, console settings APIs | Broad admin surface | Small Kanban binding form |
| Pipeline visualization | `Pipeline.tsx`, trace panels | PromptForge internals, not target workflow | Simple status timeline if needed later |
| Generic admin console CRUD | pages: `Rules`, `Templates`, `Targets`, `Health`, `Logs`, `Dashboard` | Pulls platform architecture | One review/deliver screen |

## Dependencies We Can Keep

Backend:

| Dependency | Keep? | Reason |
|---|---:|---|
| `pydantic` | yes | Contracts and validation |
| `watchdog` | yes | Filesystem watching |
| `python-frontmatter` | yes | Target explicitly prefers it |
| `PyYAML` | maybe | Only if `python-frontmatter` needs direct YAML helpers |
| `jinja2` | yes | File-based prompt templates |
| `httpx` | yes | Kanban client |
| `mdformat` | maybe | Optional markdown polish |
| `rapidfuzz` | maybe | Project/workspace fuzzy matching if needed |
| `fastapi` / `uvicorn` | yes if UI needs backend API | Minimal local HTTP API |

Frontend:

| Dependency | Keep? | Reason |
|---|---:|---|
| React/Vite/TypeScript | yes | Existing console stack |
| Tailwind | yes | Existing styling utility |
| `@tanstack/react-query` | yes | Good for preview/apply/discovery |
| `class-variance-authority`, `clsx`, `tailwind-merge` | yes if shadcn primitives kept | Small UI utility stack |
| `@radix-ui/react-slot` | maybe | Needed for current Button `asChild` |
| `@radix-ui/react-dialog/select/tabs/toast` | maybe | Keep only if those components are used |
| `lucide-react` | maybe | Icons only |

## Dependencies We Should Avoid

Backend:

| Dependency | Avoid | Reason |
|---|---:|---|
| `psycopg` | yes | Postgres out of scope |
| `libtmux` | yes | Session dispatch rejected |
| `cryptography` | yes | Secret rotation/admin settings rejected |
| LLM provider SDKs/router deps | yes | Provider routing rejected |
| `orjson` | maybe | Not needed unless performance demands it |

Frontend:

| Dependency | Avoid | Reason |
|---|---:|---|
| `recharts` | yes | Metrics/dashboard rejected |
| `cmdk` | yes | Command palette rejected |
| `react-window` | yes | Large tables rejected |
| `react-hook-form`, `zod`, resolver stack | maybe | Avoid unless forms become complex |
| `next-themes` | maybe | Use Kanban app theme tokens instead |
| Most Radix packages | yes | Only keep primitives actually rendered |
| `zustand` | maybe | Avoid global store unless config/state demands it |

## Final Recommendation

Salvage only small mechanics, not architecture.

Best approved backend ports:

1. `watcher.py` local file robustness: startup scan, debounce, temp filtering, hash dedupe.
2. `watcher.py` note loading/section extraction, rewritten around `python-frontmatter`.
3. `pipeline.py` directive/alias/render flow as concept, not as code wholesale.
4. `kanban_manifest_builder.py` almost directly.
5. `kanban_client.py` with PromptForge imports removed.

Best approved frontend ports:

1. Basic shadcn primitives only: Button/Input/Textarea/Card/Badge/Table.
2. `MarkdownPreview` after hardening.
3. Kanban preview/apply flow from `Prompts.tsx`, stripped down to one screen.
4. `ApiError` and a tiny `fetchJson` wrapper.
5. Kanban CSS variable direction, but match the modified Kanban app over old PromptForge Console.

Blunt call: reject most PromptForge Console and most PromptForge backend. The valuable code is roughly watcher robustness, simple contracts, Jinja rendering, and Kanban import glue. Everything else drags PromptForge platform assumptions into a project that should stay small.
