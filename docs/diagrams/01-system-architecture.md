# System Architecture

```graph
graph TB
    subgraph Obsidian["Obsidian Vault"]
        IntakeFolder["Intake Folder<br/>(configured watch)"]
        ProcessingFolder["Processing Folder"]
        ProcessedFolder["Processed Folder"]
    end

    subgraph Backend["FastAPI Backend (Python)"]
        Watcher["File Watcher<br/>(watchdog)"]
        IngestRuntime["Note Ingest Runtime"]
        API["REST API<br/>(FastAPI)"]
        DB[(SQLite Database)]
        KanbanClient["Kanban Client"]
    end

    subgraph Frontend["React Frontend"]
        IntakeUI["Intake Screen"]
        ReviewUI["Review Screen"]
        DeliveryUI["Deliveries Screen"]
        SettingsUI["Settings Screen"]
    end

    subgraph External["External Systems"]
        KanbanInstance["Kanban Instance<br/>(local or remote)"]
    end

    IntakeFolder -->|monitors| Watcher
    Watcher -->|new notes| IngestRuntime
    IngestRuntime -->|parse & clean| DB
    IngestRuntime -->|move processed| ProcessingFolder
    ProcessingFolder -->|approved| ProcessedFolder

    DB <-->|CRUD| API
    API <-->|HTTP/JSON| Frontend
    API -->|tRPC/HTTP| KanbanClient
    KanbanClient -->|deliver tasks| KanbanInstance

    Frontend --> IntakeUI
    Frontend --> ReviewUI
    Frontend --> DeliveryUI
    Frontend --> SettingsUI

    style Backend fill:#e1f5ff
    style Frontend fill:#fff4e6
    style Obsidian fill:#e8f5e9
    style External fill:#fce4ec
```

## Key Components

### Obsidian Vault

- **Intake Folder**: Monitored directory for new markdown notes
- **Processing Folder**: Notes currently being reviewed
- **Processed Folder**: Approved and delivered notes

### Backend (FastAPI + SQLite)

- **File Watcher**: Real-time monitoring using watchdog library
- **Ingest Runtime**: Parses markdown, extracts frontmatter, cleans intent
- **REST API**: Exposes endpoints for frontend operations
- **SQLite Database**: Stores notes, packages, steps, and deliveries
- **Kanban Client**: Capability-aware client for Kanban integration

### Frontend (React + Vite)

- **Intake Screen**: View discovered notes and their package status
- **Review Screen**: Edit prompt steps, preview payloads, approve packages
- **Deliveries Screen**: Track delivery status, view request/response, retry failures
- **Settings Screen**: Read-only configuration display

### External Systems

- **Kanban Instance**: Target system for task delivery (supports stock and forked versions)
