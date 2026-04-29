# Phase 5 Prompt — Frontend Style Alignment with Kanban

You are preparing the minimal frontend foundation for the Kanban Prompt Companion.

The frontend must visually feel like a sibling of the modified Kanban app, while remaining a separate app. It should not look like old PromptForge Console.

## Goal

Inspect the modified Kanban app styling and create a small companion UI theme/component foundation that matches it.

Do not build all screens yet. Do not port PromptForge Console shell/nav/admin pages.

## Source Inspection Required

Inspect the modified Kanban app frontend, especially:

- app shell/layout files
- Tailwind setup
- global CSS
- theme variables
- board/card styling
- buttons, inputs, dialogs, badges
- status colors
- typography
- spacing
- radius/shadow patterns

Likely Kanban paths based on previous inventory:

```text
kanban/web-ui/src/styles/globals.css
kanban/web-ui/src/main.tsx
kanban/web-ui/src/App.tsx
kanban/web-ui/src/components/kanban-board.tsx
kanban/web-ui/src/components/ui/*
kanban/web-ui/vite.config.ts
kanban/web-ui/package.json
```

Also inspect PromptForge Console only for small reusable components:

```text
prompt-forge-console/src/components/ui/button.tsx
prompt-forge-console/src/components/ui/input.tsx
prompt-forge-console/src/components/ui/textarea.tsx
prompt-forge-console/src/components/ui/badge.tsx
prompt-forge-console/src/components/ui/card.tsx
prompt-forge-console/src/components/ui/table.tsx
prompt-forge-console/src/components/pf/MarkdownPreview.tsx
prompt-forge-console/src/services/promptforge/errors.ts
prompt-forge-console/src/services/promptforge/api.ts
```

## Styling Requirements

Create or adjust:

```text
web/src/index.css
web/src/components/ui/Button.tsx
web/src/components/ui/Input.tsx
web/src/components/ui/Textarea.tsx
web/src/components/ui/Badge.tsx
web/src/components/ui/Card.tsx
web/src/components/ui/Table.tsx
web/src/components/ui/StatusBadge.tsx
```

Use Kanban’s visual language:

- same surface/background concept
- same border/radius density
- similar muted text treatment
- similar card/list spacing
- similar button density
- similar status badge treatment
- similar dark/light mode if Kanban supports it

Do not claim this app is Kanban or modify Kanban branding. It should look like a companion utility in the same local tool family.

## Component Rules

Use only components required for MVP.

Allowed:

- Button
- Input
- Textarea
- Badge
- Card
- Table
- StatusBadge
- simple toast or inline alert

Maybe allowed if needed later:

- Select
- Dialog
- Tabs

Do not port:

- PromptForge Console shell/nav/sidebar
- RoleSwitcher
- command palette
- dashboard cards/charts
- complex data grid
- query inspector
- route preview graph
- pipeline visualization
- rules/template/dictionary editors

## Markdown Preview Hardening

If adapting `MarkdownPreview`, ensure:

- no unsafe `dangerouslySetInnerHTML` unless sanitized
- code blocks render safely
- inline markdown handling does not execute HTML
- user-provided prompt content is escaped or sanitized

A simple safe renderer is acceptable, even if less feature-rich.

## API Client Foundation

Adapt only:

- tiny `fetchJson`
- tiny `postJson`
- typed `ApiError`

Do not port the full PromptForge service layer, mock hydration, or domain-specific API modules.

Target files:

```text
web/src/api/client.ts
web/src/api/errors.ts
web/src/api/types.ts
```

## Layout Foundation

Create a minimal layout that can support four screens:

```text
Intake
Review
Deliveries
Settings
```

But keep the actual implementation placeholder/minimal in this phase.

Preferred layout:

- narrow top header
- compact navigation tabs or left rail only if it matches Kanban
- main content width similar to Kanban app panels
- cards/panels that match Kanban’s board/card feel

## Required Verification

- frontend builds
- components render in a simple app shell
- no rejected PromptForge Console components imported
- no chart/command palette/global role store dependencies added
- visual tokens reference Kanban style decisions where practical

## Output Required

Return:

1. Kanban style conventions discovered.
2. Files created/changed.
3. PromptForge Console components copied/adapted/rejected.
4. Dependencies added/removed.
5. Build/test commands run.
6. Confirmation that the UI foundation matches Kanban more than PromptForge Console.
