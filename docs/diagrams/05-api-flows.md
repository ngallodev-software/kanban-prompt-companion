# API Flow Diagrams

## Review and Delivery Flow

```mermaid
sequenceDiagram
    participant UI as React UI
    participant API as FastAPI
    participant DB as SQLite
    participant Kanban as Kanban Instance

    Note over UI: User opens Review screen
    
    UI->>API: GET /api/review
    API->>DB: list_review_packages()
    DB-->>API: Packages with requires_review=true
    API-->>UI: {items: [...]}
    
    UI->>API: GET /api/kanban/workspaces
    API->>Kanban: projects.list tRPC call
    Kanban-->>API: Available workspaces
    API-->>UI: {items: [...]}
    
    UI->>API: GET /api/packages/{package_id}
    API->>DB: get_prompt_package()
    DB-->>API: Package with steps
    API-->>UI: Package detail
    
    Note over UI: User edits step
    
    UI->>API: PATCH /api/steps/{step_id}
    Note right of API: {title, prompt_markdown,<br/>base_ref, agent_id,<br/>start_in_plan_mode}
    API->>DB: update_prompt_step()
    DB-->>API: Updated step
    API-->>UI: {step: {...}}
    
    Note over UI: User previews Kanban payload
    
    UI->>API: POST /api/packages/{id}/kanban/preview
    API->>API: build_kanban_manifest()
    API->>Kanban: probe_upsert_capability()
    Kanban-->>API: true/false
    
    alt Single step + upsert capable
        API-->>UI: {procedure: "workspace.upsertTaskByExternalKey",<br/>payload: {...}}
    else Multi-step or no upsert
        API-->>UI: {procedure: "workspace.importTasks",<br/>payload: {tasks: [...]}}
    end
    
    Note over UI: User approves package
    
    UI->>API: POST /api/packages/{id}/approve
    API->>DB: mark_package_approved()
    API->>DB: mark_note_status("approved")
    API-->>UI: {package: {...}}
    
    Note over UI: User delivers to Kanban
    
    UI->>API: POST /api/packages/{id}/kanban/deliver
    API->>DB: create_delivery_preview()
    API->>DB: mark_delivery_delivering()
    
    alt upsertTaskByExternalKey
        API->>Kanban: POST workspace.upsertTaskByExternalKey
        Kanban-->>API: {task: {...}}
    else importTasks
        API->>Kanban: POST workspace.importTasks
        Kanban-->>API: {tasks: [...]}
    end
    
    alt Success
        API->>DB: mark_delivery_success()
        API->>DB: mark_prompt_package_status("delivered")
        API->>DB: mark_prompt_steps_status("delivered")
        API-->>UI: {delivery: {status: "delivered"},<br/>kanban_response: {...}}
    else Failure
        API->>DB: mark_delivery_failed()
        API->>DB: mark_prompt_package_status("failed")
        API->>DB: mark_prompt_steps_status("failed")
        API-->>UI: {delivery: {status: "failed",<br/>error_message: "..."}}
    end
```

## Intake Monitoring Flow

```mermaid
sequenceDiagram
    participant Vault as Obsidian Vault
    participant Watcher as NoteWatcher
    participant Runtime as IngestRuntime
    participant Parser as Markdown Parser
    participant Cleaner as Intent Cleaner
    participant Renderer as Template Renderer
    participant DB as SQLite

    Note over Vault: New note created<br/>in intake folder
    
    Vault->>Watcher: File system event
    Watcher->>Runtime: on_created(file_path)
    
    Runtime->>Runtime: stable_read(path)
    Note right of Runtime: Waits for file<br/>write completion
    
    Runtime->>Parser: load_note_from_path()
    Parser->>Parser: Extract frontmatter
    Parser->>Parser: Parse body
    Parser->>Parser: Extract transcript
    Parser-->>Runtime: LoadedNote
    
    Runtime->>Runtime: Dedupe check<br/>(content_hash)
    
    alt Duplicate content
        Runtime->>DB: Skip duplicate
        Runtime-->>Runtime: Exit early
    end
    
    Runtime->>Cleaner: clean_intent()
    Cleaner->>Cleaner: Apply directives<br/>(control text)
    Cleaner-->>Runtime: Cleaned text
    
    Runtime->>Renderer: render_prompt_package()
    Renderer->>Renderer: Load Jinja2 template
    Renderer->>Renderer: Build package context
    Renderer-->>Runtime: PromptPackageV1
    
    Runtime->>DB: Store note
    Runtime->>DB: Store prompt_package
    Runtime->>DB: Store prompt_steps
    
    Runtime->>Vault: Move to processing folder
    Note right of Runtime: Rename within vault
    
    Runtime->>DB: update_note_location()
    Runtime->>DB: mark_note_status("review_ready")
    
    Note over DB: Ready for human review
```

## Retry Delivery Flow

```mermaid
sequenceDiagram
    participant UI as React UI
    participant API as FastAPI
    participant DB as SQLite
    participant Kanban as Kanban Instance

    Note over UI: User views failed delivery
    
    UI->>API: GET /api/deliveries/{delivery_id}
    API->>DB: get_delivery()
    DB-->>API: Delivery record
    API-->>UI: {delivery: {status: "failed",<br/>error_message: "..."}}
    
    Note over UI: User clicks Retry
    
    UI->>API: POST /api/deliveries/{id}/retry
    API->>DB: get_delivery()
    API->>DB: get_prompt_package()
    
    API->>API: build_kanban_manifest()<br/>(fresh from current package)
    
    API->>DB: update_delivery_request()
    Note right of DB: Refreshes request payload<br/>with latest package state
    
    API->>DB: mark_delivery_delivering()
    
    alt upsertTaskByExternalKey
        API->>Kanban: POST workspace.upsertTaskByExternalKey
        Kanban-->>API: {task: {...}}
    else importTasks
        API->>Kanban: POST workspace.importTasks
        Kanban-->>API: {tasks: [...]}
    end
    
    alt Success
        API->>DB: mark_delivery_success()
        API->>DB: mark_prompt_package_status("delivered")
        API->>DB: mark_prompt_steps_status("delivered")
        API-->>UI: {delivery: {status: "delivered"},<br/>kanban_response: {...}}
    else Failure Again
        API->>DB: mark_delivery_failed()
        API->>DB: mark_prompt_package_status("failed")
        API->>DB: mark_prompt_steps_status("failed")
        API-->>UI: {delivery: {status: "failed",<br/>error_message: "..."}}
    end
```

## Key API Endpoints

### Intake
- `GET /api/intake` - List notes with optional status filter
- `GET /api/intake/{note_id}` - Note detail with latest package

### Review
- `GET /api/review` - List packages requiring review
- `GET /api/packages/{package_id}` - Package detail with steps
- `PATCH /api/steps/{step_id}` - Update step fields
- `PATCH /api/packages/{package_id}` - Update workspace
- `POST /api/packages/{package_id}/approve` - Approve package

### Kanban Integration
- `GET /api/kanban/workspaces` - List Kanban workspaces
- `POST /api/packages/{id}/kanban/preview` - Preview payload
- `POST /api/packages/{id}/kanban/deliver` - Deliver to Kanban

### Deliveries
- `GET /api/deliveries` - List all delivery attempts
- `GET /api/deliveries/{delivery_id}` - Delivery detail
- `POST /api/deliveries/{delivery_id}/retry` - Retry failed delivery
