# Kanban Prompt Companion - Diagrams

This directory contains comprehensive architectural diagrams for the Kanban Prompt Companion system.

## Diagram Index

### 1. System Architecture (`01-system-architecture.md`)
High-level overview of the complete system showing:
- Obsidian Vault integration
- Backend services (FastAPI + SQLite)
- Frontend UI (React)
- External Kanban integration

**Use this when:** You need to understand the overall system layout and component boundaries.

### 2. Data Flow (`02-data-flow.md`)
End-to-end sequence showing the journey from note to delivered Kanban task:
- Note discovery and ingestion
- Human review and editing
- Kanban delivery and retry

**Use this when:** You need to trace how data moves through the system from start to finish.

### 3. Component Structure (`03-component-structure.md`)
Detailed breakdown of backend and frontend components:
- Backend modules (CLI, API, Ingest, Storage, Kanban)
- Frontend modules (Screens, API Client, UI components)

**Use this when:** You need to understand the internal organization of the codebase.

### 4. Database Schema (`04-database-schema.md`)
SQLite database structure with:
- Entity-relationship diagram
- Table definitions and constraints
- Indexes and relationships

**Use this when:** You need to understand data persistence and relationships.

### 5. API Flows (`05-api-flows.md`)
Detailed sequence diagrams for key operations:
- Review and delivery flow
- Intake monitoring flow
- Retry delivery flow
- Complete API endpoint reference

**Use this when:** You need to understand specific API interactions or implement new features.

### 6. Kanban Integration (`06-kanban-integration.md`)
Capability detection and Kanban-specific integration:
- Endpoint selection logic
- Stock vs. forked Kanban support
- Request/response formats
- Error handling strategy

**Use this when:** You need to understand or modify Kanban integration behavior.

## Viewing the Diagrams

All diagrams use Mermaid syntax and can be viewed:

1. **In GitHub:** Native Mermaid rendering in markdown preview
2. **In VS Code:** Install the "Markdown Preview Mermaid Support" extension
3. **In Obsidian:** Native support or use the "Mermaid" plugin
4. **Online:** Copy/paste into [Mermaid Live Editor](https://mermaid.live/)

## Diagram Maintenance

When updating the codebase:
- **Add new components:** Update `03-component-structure.md`
- **Change database schema:** Update `04-database-schema.md`
- **Add API endpoints:** Update `05-api-flows.md`
- **Modify integration:** Update `06-kanban-integration.md`
- **Architectural changes:** Update `01-system-architecture.md` and `02-data-flow.md`

## Quick Reference

| Need to understand... | Start with... |
|---|---|
| Overall system design | `01-system-architecture.md` |
| Note-to-task workflow | `02-data-flow.md` |
| Code organization | `03-component-structure.md` |
| Data model | `04-database-schema.md` |
| API behavior | `05-api-flows.md` |
| Kanban delivery | `06-kanban-integration.md` |

## Contributing

When adding diagrams:
1. Use Mermaid syntax for consistency
2. Keep diagrams focused (one concept per diagram)
3. Include descriptive text below diagrams
4. Update this README with the new diagram
5. Use semantic file naming: `##-descriptive-name.md`
