from __future__ import annotations

import json
import time
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import AppConfig
from app.kanban.client import KanbanClient, KanbanClientConfig
from app.main import create_app
from app.storage import get_note


def _templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def _fixture_text(title: str, transcript: str) -> str:
    return f"""---
title: {title}
status: new
watch_eligible: true
---

## Control
project is kanban
workspace is kanban
harness is codex
base ref is main

## Transcript
{transcript}
"""


def _wait_for(predicate, *, timeout_seconds: float = 8.0, poll_interval_seconds: float = 0.1):
    deadline = time.monotonic() + timeout_seconds
    last_value = None
    while time.monotonic() < deadline:
        last_value = predicate()
        if last_value:
            return last_value
        time.sleep(poll_interval_seconds)
    raise AssertionError(f"timed out waiting for condition; last_value={last_value!r}")


def test_running_workflow_processes_notes_from_disk_and_delivers_them(tmp_path: Path) -> None:
    vault_path = tmp_path / "Vault"
    watch_folder = "Inbox/Voice"
    note_root = vault_path / watch_folder
    note_root.mkdir(parents=True, exist_ok=True)

    startup_note_path = note_root / "startup-note.md"
    startup_note_path.write_text(
        _fixture_text(
            "Startup watcher note",
            "Um, add a startup scan so existing notes are picked up when the app launches.",
        ),
        encoding="utf-8",
    )

    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/workspace.getState"):
            return httpx.Response(200, json={"result": {"data": {"json": {"canUpsertTaskByExternalKey": True}}}})
        if request.url.path.endswith("/workspace.upsertTaskByExternalKey"):
            payload = json.loads(request.content.decode("utf-8"))
            return httpx.Response(
                200,
                json={
                    "result": {
                        "data": {
                            "json": {
                                "ok": True,
                                "mode": "upsert",
                                "title": payload["title"],
                                "prompt": payload["prompt"],
                            }
                        }
                    }
                },
            )
        raise AssertionError(request.url.path)

    app = create_app(
        AppConfig(
            vault_path=vault_path,
            watch_folder=watch_folder,
            processing_folder="Processing/Voice",
            processed_folder="Processed/Voice",
            database_path=tmp_path / "state.sqlite3",
            kanban_base_url="http://kanban.local",
            kanban_workspace_id="kanban",
            template_dir=_templates_dir(),
        ),
        kanban_client=KanbanClient(
            KanbanClientConfig(base_url="http://kanban.local", workspace_id="kanban"),
            transport=httpx.MockTransport(handler),
        ),
    )

    with TestClient(app) as client:
        startup_intake = _wait_for(lambda: client.get("/api/intake").json()["items"])
        assert any(item["title"] == "Startup watcher note" for item in startup_intake)

        live_note_path = note_root / "live-note.md"
        live_note_path.write_text(
            _fixture_text(
                "Live watcher note",
                "I need you to add a live filesystem watcher path and keep the Kanban delivery flow intact.",
            ),
            encoding="utf-8",
        )

        live_note_id = _wait_for(
            lambda: next(
                (
                    item["id"]
                    for item in client.get("/api/intake").json()["items"]
                    if item["title"] == "Live watcher note" and item["status"] in {"parsed", "review_ready"}
                ),
                None,
            )
        )

        review_package_id = _wait_for(
            lambda: next(
                (
                    item["id"]
                    for item in client.get("/api/review").json()["items"]
                    if item["note_title"] == "Live watcher note"
                ),
                None,
            )
        )

        note_detail = client.get(f"/api/intake/{live_note_id}")
        assert note_detail.status_code == 200
        assert "live filesystem watcher path" in note_detail.json()["transcript"]

        preview = client.post(f"/api/packages/{review_package_id}/kanban/preview")
        assert preview.status_code == 200
        assert preview.json()["procedure"] == "workspace.upsertTaskByExternalKey"

        deliver = client.post(f"/api/packages/{review_package_id}/kanban/deliver")
        assert deliver.status_code == 200
        assert deliver.json()["delivery"]["status"] == "delivered"
        assert deliver.json()["kanban_response"]["mode"] == "upsert"

        assert get_note(app.state.db_connection, live_note_id).status == "review_ready"
        assert calls.count("/api/trpc/workspace.getState") >= 2
        assert "/api/trpc/workspace.upsertTaskByExternalKey" in calls


def test_workspace_selection_is_persisted_and_used_for_preview(tmp_path: Path) -> None:
    vault_path = tmp_path / "Vault"
    watch_folder = "Inbox/Voice"
    note_root = vault_path / watch_folder
    note_root.mkdir(parents=True, exist_ok=True)

    note_path = note_root / "workspace-note.md"
    note_path.write_text(
        _fixture_text(
            "Workspace choice note",
            "Choose the correct Kanban project before previewing the task.",
        ),
        encoding="utf-8",
    )

    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/projects.list"):
            return httpx.Response(
                200,
                json={
                    "result": {
                        "data": {
                            "json": {
                                "currentProjectId": "kanban",
                                "projects": [
                                    {"id": "kanban", "name": "Kanban", "path": "/vault/kanban"},
                                    {"id": "product", "name": "Product", "path": "/vault/product"},
                                ],
                            }
                        }
                    },
                },
            )
        if request.url.path.endswith("/workspace.getState"):
            return httpx.Response(200, json={"result": {"data": {"json": {"canUpsertTaskByExternalKey": True}}}})
        raise AssertionError(request.url.path)

    app = create_app(
        AppConfig(
            vault_path=vault_path,
            watch_folder=watch_folder,
            processing_folder="Processing/Voice",
            processed_folder="Processed/Voice",
            database_path=tmp_path / "state.sqlite3",
            kanban_base_url="http://kanban.local",
            kanban_workspace_id="kanban",
            template_dir=_templates_dir(),
        ),
        kanban_client=KanbanClient(
            KanbanClientConfig(base_url="http://kanban.local", workspace_id="kanban"),
            transport=httpx.MockTransport(handler),
        ),
    )

    with TestClient(app) as client:
        _wait_for(lambda: client.get("/api/intake").json()["items"])

        workspaces = client.get("/api/kanban/workspaces")
        assert workspaces.status_code == 200
        assert [item["id"] for item in workspaces.json()["items"]] == ["kanban", "product"]

        package_id = _wait_for(
            lambda: next(
                (
                    item["id"]
                    for item in client.get("/api/review").json()["items"]
                    if item["note_title"] == "Workspace choice note"
                ),
                None,
            )
        )

        update = client.patch(f"/api/packages/{package_id}", json={"workspace_id": "product"})
        assert update.status_code == 200
        assert update.json()["package"]["workspace_id"] == "product"

        preview = client.post(f"/api/packages/{package_id}/kanban/preview")
        assert preview.status_code == 200
        assert preview.json()["workspace_id"] == "product"
        assert calls.count("/api/trpc/projects.list") == 1


def test_note_moves_to_processing_then_processed_and_survives_delivery_failure(tmp_path: Path) -> None:
    vault_path = tmp_path / "Vault"
    watch_folder = "Inbox/Voice"
    processing_folder = "Processing/Voice"
    processed_folder = "Processed/Voice"
    note_root = vault_path / watch_folder
    note_root.mkdir(parents=True, exist_ok=True)

    note_path = note_root / "move-me.md"
    note_path.write_text(
        _fixture_text(
            "Move me note",
            "Move me through processing and review, then let delivery fail without touching the file.",
        ),
        encoding="utf-8",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/workspace.getState"):
            return httpx.Response(200, json={"result": {"data": {"json": {"canUpsertTaskByExternalKey": True}}}})
        if request.url.path.endswith("/workspace.upsertTaskByExternalKey"):
            return httpx.Response(500, json={"error": {"message": "delivery failed"}})
        raise AssertionError(request.url.path)

    app = create_app(
        AppConfig(
            vault_path=vault_path,
            watch_folder=watch_folder,
            processing_folder=processing_folder,
            processed_folder=processed_folder,
            database_path=tmp_path / "state.sqlite3",
            kanban_base_url="http://kanban.local",
            kanban_workspace_id="kanban",
            template_dir=_templates_dir(),
        ),
        kanban_client=KanbanClient(
            KanbanClientConfig(base_url="http://kanban.local", workspace_id="kanban"),
            transport=httpx.MockTransport(handler),
        ),
    )

    with TestClient(app) as client:
        package_id = _wait_for(
            lambda: next(
                (
                    item["id"]
                    for item in client.get("/api/review").json()["items"]
                    if item["note_title"] == "Move me note"
                ),
                None,
            )
        )

        assert not note_path.exists()
        processing_path = vault_path / processing_folder / "move-me.md"
        assert processing_path.exists()

        approve = client.post(f"/api/packages/{package_id}/approve")
        assert approve.status_code == 200
        assert approve.json()["package"]["status"] == "approved"

        processed_path = vault_path / processed_folder / "move-me.md"
        assert processed_path.exists()
        assert not processing_path.exists()
        assert get_note(app.state.db_connection, approve.json()["package"]["note_id"]).absolute_path == str(processed_path)

        deliver = client.post(f"/api/packages/{package_id}/kanban/deliver")
        assert deliver.status_code == 200
        assert deliver.json()["delivery"]["status"] == "failed"
        assert processed_path.exists()
        assert get_note(app.state.db_connection, approve.json()["package"]["note_id"]).absolute_path == str(processed_path)
