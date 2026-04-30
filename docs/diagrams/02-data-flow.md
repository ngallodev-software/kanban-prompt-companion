# Data Flow: Note to Kanban Task

```mermaid
sequenceDiagram
    participant Vault as Obsidian Vault
    participant Watcher as File Watcher
    participant Ingest as Ingest Runtime
    participant DB as SQLite DB
    participant UI as React UI
    participant API as FastAPI
    participant Kanban as Kanban Instance

    Note over Vault: User creates note<br/>in intake folder
    
    Vault->>Watcher: File created event
    Watcher->>Ingest: New note detected
    
    Ingest->>Ingest: Parse markdown<br/>Extract frontmatter<br/>Clean intent
    Ingest->>DB: Store note (discovered)
    Ingest->>DB: Create prompt package<br/>(review_ready)
    Ingest->>Vault: Move to processing folder
    
    Note over DB: Note status: review_ready<br/>Package requires_review: true
    
    UI->>API: GET /api/review
    API->>DB: List review packages
    DB-->>API: Review queue
    API-->>UI: Display packages
    
    Note over UI: Human reviews<br/>and edits steps
    
    UI->>API: PATCH /api/steps/{id}
    API->>DB: Update step
    DB-->>UI: Confirm save
    
    UI->>API: POST /api/packages/{id}/kanban/preview
    API->>API: Build manifest
    API-->>UI: Show Kanban payload
    
    Note over UI: Human approves delivery
    
    UI->>API: POST /api/packages/{id}/kanban/deliver
    API->>DB: Mark package delivering
    API->>Kanban: workspace.upsertTaskByExternalKey<br/>OR workspace.importTasks
    
    alt Delivery Success
        Kanban-->>API: Task created response
        API->>DB: Mark delivered
        API->>Vault: Move to processed folder
        API-->>UI: Success + response
    else Delivery Failure
        Kanban-->>API: Error response
        API->>DB: Mark failed + error message
        API-->>UI: Failure + retry option
    end
    
    Note over DB: Package status: delivered<br/>Note status: delivered
```

## Flow Stages

### 1. Ingestion (Automatic)
- File watcher detects new note
- Markdown parsed, frontmatter extracted
- Intent cleaned and packaged
- Note moved to processing folder
- Status: `discovered` → `review_ready`

### 2. Review (Human-in-the-loop)
- Review queue populated
- Human edits prompt steps
- Preview Kanban payload
- Workspace selection

### 3. Approval (Manual Trigger)
- Package marked approved
- Note moved to processed folder
- Optional: Immediate delivery

### 4. Delivery (API-driven)
- Build Kanban manifest
- Capability detection (upsert vs import)
- Submit to Kanban instance
- Record response or error

### 5. Retry (Optional)
- Delivery failures can be retried
- Refreshes payload from current package state
- Re-attempts Kanban submission
