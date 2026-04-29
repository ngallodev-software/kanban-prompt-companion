from __future__ import annotations

import logging
import sqlite3
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from app.config import AppConfig, load_config
from app.contracts import HealthResponse, PromptPackageV1
from app.kanban.client import KanbanClient, KanbanClientConfig, KanbanClientError, KanbanTransportError
from app.kanban.manifest import build_kanban_manifest
from app.storage import (
    create_delivery_preview,
    get_delivery,
    get_latest_prompt_package_for_note,
    get_note,
    get_prompt_package,
    list_deliveries,
    list_notes,
    list_review_packages,
    mark_delivery_delivering,
    mark_delivery_failed,
    mark_delivery_success,
    mark_note_status,
    mark_package_approved,
    mark_prompt_package_status,
    mark_prompt_steps_status,
    update_delivery_request,
    update_prompt_step,
)
from app.storage.db import connect_database

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


class StepUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    prompt_markdown: str | None = None
    base_ref: str | None = None
    agent_id: str | None = None
    start_in_plan_mode: bool | None = None


class ApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deliver: bool = False


def create_app(
    config: AppConfig | None = None,
    *,
    db_connection: sqlite3.Connection | None = None,
    kanban_client: KanbanClient | None = None,
) -> FastAPI:
    app_config = config or load_config()
    app = FastAPI(title="Kanban Prompt Companion", version="0.1.0")
    app.state.config = app_config
    app.state.db_connection = db_connection
    app.state.kanban_client = kanban_client
    app.state.owns_db_connection = db_connection is None

    @app.on_event("startup")
    def startup() -> None:
        if getattr(app.state, "db_connection", None) is None:
            app.state.db_connection = connect_database(app.state.config.database_path)
            app.state.owns_db_connection = True
        if getattr(app.state, "kanban_client", None) is None:
            app.state.kanban_client = KanbanClient(
                KanbanClientConfig(
                    base_url=str(app.state.config.kanban_base_url),
                    workspace_id=_configured_workspace_id(app),
                )
            )

    @app.on_event("shutdown")
    def shutdown() -> None:
        connection = getattr(app.state, "db_connection", None)
        if connection is not None and getattr(app.state, "owns_db_connection", False):
            connection.close()
            app.state.db_connection = None

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(ok=True)

    @app.get("/api/intake")
    def intake(status: str | None = None, limit: int | None = None) -> dict[str, Any]:
        connection = _db(app)
        notes = list_notes(connection, status=status, limit=limit)
        return {"items": [_serialize_intake_note(connection, note) for note in notes]}

    @app.get("/api/intake/{note_id}")
    def intake_detail(note_id: str) -> dict[str, Any]:
        connection = _db(app)
        try:
            note = get_note(connection, note_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="note not found") from exc
        package = get_latest_prompt_package_for_note(connection, note_id)
        return _serialize_note_detail(connection, note, package)

    @app.get("/api/review")
    def review_queue() -> dict[str, Any]:
        connection = _db(app)
        packages = list_review_packages(connection)
        return {"items": [_serialize_package_summary(connection, package) for package in packages]}

    @app.get("/api/packages/{package_id}")
    def package_detail(package_id: str) -> dict[str, Any]:
        connection = _db(app)
        package = _get_package(connection, package_id)
        return _serialize_package_detail(connection, package)

    @app.patch("/api/steps/{step_id}")
    def patch_step(step_id: str, body: StepUpdateRequest) -> dict[str, Any]:
        connection = _db(app)
        try:
            step = update_prompt_step(
                connection,
                step_id,
                title=body.title,
                prompt_markdown=body.prompt_markdown,
                base_ref=body.base_ref,
                agent_id=body.agent_id,
                start_in_plan_mode=body.start_in_plan_mode,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="step not found") from exc
        return {"step": _serialize_step(step)}

    @app.post("/api/packages/{package_id}/approve")
    def approve_package(package_id: str, body: ApproveRequest | None = None) -> dict[str, Any]:
        connection = _db(app)
        approved = mark_package_approved(connection, package_id)
        response: dict[str, Any] = {"package": _serialize_package_detail(connection, approved)}
        if body and body.deliver:
            response["delivery"] = _deliver_package(connection, approved, app)
        return response

    @app.get("/api/kanban/workspaces")
    def kanban_workspaces() -> dict[str, Any]:
        client = _kanban(app)
        try:
            projects = client.list_projects()
        except KanbanTransportError as exc:
            raise HTTPException(status_code=502, detail=f"kanban connection error: {exc}") from exc
        except KanbanClientError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {"items": [_normalize_workspace(project) for project in projects]}

    @app.post("/api/packages/{package_id}/kanban/preview")
    def kanban_preview(package_id: str) -> dict[str, Any]:
        connection = _db(app)
        package = _get_package(connection, package_id)
        preview = _build_kanban_plan(connection, package, app)
        return {"package_id": package.id, **preview}

    @app.post("/api/packages/{package_id}/kanban/deliver")
    def kanban_deliver(package_id: str) -> dict[str, Any]:
        connection = _db(app)
        package = _get_package(connection, package_id)
        return _deliver_package(connection, package, app)

    @app.get("/api/deliveries")
    def deliveries() -> dict[str, Any]:
        connection = _db(app)
        return {"items": [_serialize_delivery(connection, record) for record in list_deliveries(connection)]}

    @app.get("/api/deliveries/{delivery_id}")
    def delivery_detail(delivery_id: str) -> dict[str, Any]:
        connection = _db(app)
        try:
            delivery = get_delivery(connection, delivery_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="delivery not found") from exc
        return {"delivery": _serialize_delivery(connection, delivery)}

    @app.post("/api/deliveries/{delivery_id}/retry")
    def retry_delivery(delivery_id: str) -> dict[str, Any]:
        connection = _db(app)
        try:
            delivery = get_delivery(connection, delivery_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="delivery not found") from exc
        package = _get_package(connection, delivery.package_id)
        return _retry_delivery(connection, delivery, package, app)

    return app


def _db(app: FastAPI) -> sqlite3.Connection:
    connection = getattr(app.state, "db_connection", None)
    if connection is None:
        raise RuntimeError("database connection not initialized")
    return connection


def _kanban(app: FastAPI) -> KanbanClient:
    client = getattr(app.state, "kanban_client", None)
    if client is None:
        raise RuntimeError("kanban client not initialized")
    return client


def _configured_workspace_id(app: FastAPI) -> str | None:
    raw = getattr(app.state.config, "kanban_workspace_id", None)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _get_package(connection: sqlite3.Connection, package_id: str):
    try:
        return get_prompt_package(connection, package_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="package not found") from exc


def _package_model(connection: sqlite3.Connection, package, app: FastAPI) -> PromptPackageV1:
    note = get_note(connection, package.note_id)
    return PromptPackageV1(
        source_note_path=note.absolute_path,
        source_note_title=note.title,
        source_note_hash=note.content_hash,
        title=note.title,
        cleaned_intent=package.cleaned_intent,
        project_key=package.project_key or str(note.frontmatter.get("project") or "kanban"),
        workspace_id=_resolve_workspace_id(app, package.kanban_workspace_id),
        steps=[
            {
                "step_index": step.step_index,
                "title": step.title,
                "prompt_markdown": step.prompt_markdown,
                "external_task_key": step.external_task_key,
                "base_ref": step.base_ref,
                "agent_id": step.agent_id,
                "start_in_plan_mode": bool(step.start_in_plan_mode),
                "depends_on_step_indices": step.depends_on_step_indices,
                "step_intent": "",
                "cleanup_notes": [],
                "guardrails": {"items": []},
                "verification": {"commands": [], "notes": []},
            }
            for step in package.steps
        ],
    )


def _build_kanban_plan(
    connection: sqlite3.Connection,
    package,
    app: FastAPI,
) -> dict[str, Any]:
    package_model = _package_model(connection, package, app)
    manifest = build_kanban_manifest(package_model)
    workspace_id = _resolve_workspace_id(app, package.kanban_workspace_id)
    if workspace_id is None:
        raise HTTPException(status_code=400, detail="kanban workspace id is required")

    client = _kanban(app)
    if len(manifest.tasks) == 1 and client.probe_upsert_capability(workspace_id):
        procedure = "workspace.upsertTaskByExternalKey"
        payload = manifest.tasks[0].model_dump(by_alias=True, exclude_none=True)
    else:
        procedure = "workspace.importTasks"
        payload = manifest.model_dump(by_alias=True, exclude_none=True)
    return {"workspace_id": workspace_id, "procedure": procedure, "payload": payload, "warnings": []}


def _resolve_workspace_id(app: FastAPI, package_workspace_id: str | None = None) -> str | None:
    for candidate in (package_workspace_id, _configured_workspace_id(app)):
        if candidate is None:
            continue
        text = str(candidate).strip()
        if text:
            return text
    return None


def _deliver_package(connection: sqlite3.Connection, package, app: FastAPI) -> dict[str, Any]:
    preview = _build_kanban_plan(connection, package, app)
    delivery = create_delivery_preview(connection, package.id, preview["workspace_id"], preview)
    delivery = update_delivery_request(connection, delivery.id, preview, kanban_workspace_id=preview["workspace_id"])
    return _perform_delivery(connection, package, delivery, preview, app)


def _perform_delivery(
    connection: sqlite3.Connection,
    package,
    delivery,
    preview: dict[str, Any],
    app: FastAPI,
) -> dict[str, Any]:
    client = _kanban(app)
    workspace_id = preview["workspace_id"]
    if workspace_id is None:
        raise HTTPException(status_code=400, detail="kanban workspace id is required")

    mark_delivery_delivering(connection, delivery.id)
    try:
        package_model = _package_model(connection, package, app)
        manifest = build_kanban_manifest(package_model)
        if preview["procedure"] == "workspace.upsertTaskByExternalKey":
            response_payload = client.upsert_task_by_external_key(manifest.tasks[0], workspace_id=workspace_id)
        else:
            response_payload = client.import_tasks(manifest, workspace_id=workspace_id)
        delivered = mark_delivery_success(connection, delivery.id, response_payload=response_payload)
        mark_prompt_package_status(connection, package.id, status="delivered", requires_review=False)
        mark_prompt_steps_status(connection, package.id, status="delivered")
        mark_note_status(connection, package.note_id, "delivered")
        return {"delivery": _serialize_delivery(connection, delivered), "kanban_response": response_payload}
    except KanbanTransportError as exc:
        failed = mark_delivery_failed(connection, delivery.id, error_message=f"kanban connection error: {exc}")
        mark_prompt_package_status(connection, package.id, status="failed", requires_review=True, error_message=str(exc))
        mark_prompt_steps_status(connection, package.id, status="failed")
        mark_note_status(connection, package.note_id, "failed", error_message=str(exc))
        return {"delivery": _serialize_delivery(connection, failed)}
    except KanbanClientError as exc:
        failed = mark_delivery_failed(connection, delivery.id, error_message=str(exc))
        mark_prompt_package_status(connection, package.id, status="failed", requires_review=True, error_message=str(exc))
        mark_prompt_steps_status(connection, package.id, status="failed")
        mark_note_status(connection, package.note_id, "failed", error_message=str(exc))
        return {"delivery": _serialize_delivery(connection, failed)}


def _retry_delivery(connection: sqlite3.Connection, delivery, package, app: FastAPI) -> dict[str, Any]:
    preview = _build_kanban_plan(connection, package, app)
    refreshed = update_delivery_request(
        connection,
        delivery.id,
        preview,
        kanban_workspace_id=preview["workspace_id"],
    )
    return _perform_delivery(connection, package, refreshed, preview, app)


def _serialize_intake_note(connection: sqlite3.Connection, note) -> dict[str, Any]:
    package = get_latest_prompt_package_for_note(connection, note.id)
    return {
        "id": note.id,
        "status": note.status,
        "title": note.title,
        "relative_path": note.relative_path,
        "discovered_at": note.discovered_at,
        "last_seen_at": note.last_seen_at,
        "error_message": note.error_message,
        "package": _package_link(package),
    }


def _serialize_note_detail(connection: sqlite3.Connection, note, package) -> dict[str, Any]:
    result = {
        "id": note.id,
        "status": note.status,
        "title": note.title,
        "relative_path": note.relative_path,
        "absolute_path": note.absolute_path,
        "discovered_at": note.discovered_at,
        "last_seen_at": note.last_seen_at,
        "error_message": note.error_message,
        "transcript": note.raw_transcript,
        "raw_body": note.raw_body,
        "frontmatter": note.frontmatter,
        "package": _package_link(package),
    }
    if package is not None:
        result["cleaned_intent"] = package.cleaned_intent
    return result


def _package_link(package) -> dict[str, Any] | None:
    if package is None:
        return None
    return {
        "id": package.id,
        "status": package.status,
        "requires_review": bool(package.requires_review),
        "workspace_id": package.kanban_workspace_id,
        "step_count": len(package.steps),
    }


def _serialize_package_summary(connection: sqlite3.Connection, package) -> dict[str, Any]:
    note = get_note(connection, package.note_id)
    return {
        "id": package.id,
        "note_id": package.note_id,
        "note_title": note.title,
        "source_note_path": note.absolute_path,
        "source_note_title": note.title,
        "status": package.status,
        "requires_review": bool(package.requires_review),
        "workspace_id": package.kanban_workspace_id,
        "created_at": package.created_at,
        "updated_at": package.updated_at,
        "step_count": len(package.steps),
    }


def _serialize_package_detail(connection: sqlite3.Connection, package) -> dict[str, Any]:
    note = get_note(connection, package.note_id)
    return {
        "id": package.id,
        "note_id": package.note_id,
        "note_title": note.title,
        "source_note_path": note.absolute_path,
        "source_note_title": note.title,
        "status": package.status,
        "requires_review": bool(package.requires_review),
        "workspace_id": package.kanban_workspace_id,
        "cleaned_intent": package.cleaned_intent,
        "project_key": package.project_key,
        "version": package.version,
        "created_at": package.created_at,
        "updated_at": package.updated_at,
        "error_message": package.error_message,
        "steps": [_serialize_step(step) for step in package.steps],
    }


def _serialize_step(step) -> dict[str, Any]:
    return {
        "id": step.id,
        "package_id": step.package_id,
        "step_index": step.step_index,
        "external_task_key": step.external_task_key,
        "title": step.title,
        "prompt_markdown": step.prompt_markdown,
        "base_ref": step.base_ref,
        "agent_id": step.agent_id,
        "start_in_plan_mode": bool(step.start_in_plan_mode),
        "depends_on_step_indices": step.depends_on_step_indices,
        "status": step.status,
        "created_at": step.created_at,
        "updated_at": step.updated_at,
    }


def _serialize_delivery(connection: sqlite3.Connection, delivery) -> dict[str, Any]:
    package = get_prompt_package(connection, delivery.package_id)
    note = get_note(connection, package.note_id)
    return {
        "id": delivery.id,
        "package_id": delivery.package_id,
        "source_note_id": package.note_id,
        "source_note_title": note.title,
        "source_note_path": note.absolute_path,
        "kanban_workspace_id": delivery.kanban_workspace_id,
        "request": delivery.request,
        "response": delivery.response,
        "status": delivery.status,
        "error_message": delivery.error_message,
        "created_at": delivery.created_at,
        "delivered_at": delivery.delivered_at,
    }


def _normalize_workspace(project: Any) -> dict[str, Any]:
    if not isinstance(project, dict):
        return {"id": str(project), "name": str(project), "path": None}
    workspace_id = project.get("id") or project.get("workspace_id") or project.get("workspaceId")
    name = project.get("name") or project.get("title") or str(workspace_id or "workspace")
    path = project.get("path") or project.get("rootPath") or project.get("relativePath")
    return {
        "id": workspace_id,
        "name": name,
        "path": path,
    }


app = create_app()
