# Component Structure

## Backend Architecture

```mermaid
graph TB
    subgraph CLI["CLI Layer"]
        CLIMain["app/cli.py<br/>Entry point"]
    end

    subgraph API["API Layer (app/main.py)"]
        FastAPI["FastAPI Application"]
        Routes["REST Endpoints<br/>/api/intake, /api/review, etc."]
    end

    subgraph Ingest["Ingest Pipeline"]
        Watcher["NoteWatcher<br/>(watchdog)"]
        Runtime["NoteIngestRuntime"]
        Markdown["markdown.py<br/>Parser"]
        Cleanup["cleanup.py<br/>Intent cleaner"]
        Render["render.py<br/>Template renderer"]
        Lifecycle["lifecycle.py<br/>File operations"]
    end

    subgraph Storage["Storage Layer"]
        Repo["repository.py<br/>CRUD operations"]
        Schema["schema.py<br/>Table definitions"]
        DBConn["db.py<br/>Connection manager"]
    end

    subgraph Integration["Kanban Integration"]
        Client["client.py<br/>HTTP client"]
        Manifest["manifest.py<br/>Payload builder"]
    end

    subgraph Models["Domain Models"]
        Contracts["contracts.py<br/>PromptPackageV1<br/>PromptStepV1"]
    end

    CLIMain --> FastAPI
    FastAPI --> Routes
    Routes --> Runtime
    Routes --> Repo
    Routes --> Client
    
    Runtime --> Watcher
    Runtime --> Markdown
    Runtime --> Cleanup
    Runtime --> Render
    Runtime --> Lifecycle
    Runtime --> Repo
    
    Client --> Manifest
    Manifest --> Contracts
    
    Repo --> Schema
    Repo --> DBConn
    
    style API fill:#e1f5ff
    style Ingest fill:#fff4e6
    style Storage fill:#e8f5e9
    style Integration fill:#fce4ec
```

## Frontend Architecture

```mermaid
graph TB
    subgraph App["App.tsx"]
        Router["Client-side Router<br/>useBrowserLocation"]
        Layout["Layout Shell<br/>Header + Nav"]
    end

    subgraph Screens["Screen Components"]
        Intake["IntakeScreen"]
        Review["ReviewScreen"]
        Deliveries["DeliveriesScreen"]
        Settings["SettingsScreen"]
    end

    subgraph API_Client["API Layer"]
        Client["api/client.ts<br/>HTTP utilities"]
        KPC["api/kanbanPromptCompanion.ts<br/>API functions"]
        Types["api/types.ts<br/>TypeScript types"]
    end

    subgraph State["State Management"]
        ReactQuery["@tanstack/react-query<br/>Server state"]
        LocalState["useState hooks<br/>UI state"]
    end

    subgraph UI["UI Components"]
        Cards["ui/Card.tsx"]
        Buttons["ui/Button.tsx"]
        Tables["ui/Table.tsx"]
        Forms["ui/Input.tsx<br/>ui/Textarea.tsx"]
        Badge["ui/StatusBadge.tsx"]
        SafeMD["SafeMarkdownPreview.tsx"]
    end

    Router --> Intake
    Router --> Review
    Router --> Deliveries
    Router --> Settings
    
    Intake --> ReactQuery
    Review --> ReactQuery
    Deliveries --> ReactQuery
    Settings --> Client
    
    ReactQuery --> KPC
    KPC --> Client
    Client --> Types
    
    Intake --> UI
    Review --> UI
    Deliveries --> UI
    Settings --> UI
    
    Review --> SafeMD
    
    style App fill:#e1f5ff
    style Screens fill:#fff4e6
    style State fill:#e8f5e9
    style UI fill:#fce4ec
```

## Key Backend Modules

### app/main.py
- FastAPI application factory
- Route definitions
- Dependency injection (DB, Kanban client)

### app/ingest/
- **watcher.py**: File system monitoring
- **runtime.py**: Orchestrates ingestion pipeline
- **markdown.py**: Frontmatter + body parsing
- **cleanup.py**: Intent extraction and cleaning
- **render.py**: Jinja2 template rendering for prompts

### app/storage/
- **repository.py**: Database CRUD operations
- **schema.py**: SQLite table definitions
- **db.py**: Connection and initialization

### app/kanban/
- **client.py**: HTTP client with capability detection
- **manifest.py**: Converts PromptPackageV1 to Kanban format

## Key Frontend Modules

### src/App.tsx
- Single-page application shell
- Client-side routing
- Screen orchestration

### src/api/
- **kanbanPromptCompanion.ts**: Typed API functions
- **client.ts**: HTTP request utilities
- **types.ts**: TypeScript type definitions

### src/components/ui/
- Reusable UI primitives
- Consistent styling with Tailwind
