from __future__ import annotations

import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import AppConfig
from app.contracts import LoadedNote, PromptPackageV1, PromptStepV1
from app.ingest.dedupe import sha256_content_hash
from app.main import create_app
from app.kanban.client import KanbanClient, KanbanClientConfig
from app.storage import create_prompt_package, get_note, list_deliveries, upsert_note_from_loaded_note
from app.storage.db import connect_database


def _note(*, title: str, relative_path: str, transcript: str) -> LoadedNote:
    return LoadedNote(
        absolute_path=f"/vault/{relative_path}",
        relative_path=relative_path,
        title=title,
        frontmatter={"project": "kanban"},
        body=transcript,
        control_text=None,
        transcript_text=transcript,
        content_hash=sha256_content_hash(transcript),
    )


def _package(note: LoadedNote, *, steps: list[PromptStepV1]) -> PromptPackageV1:
    return PromptPackageV1(
        source_note_path=note.absolute_path,
        cleaned_intent=steps[0].prompt_markdown if len(steps) == 1 else "Split the task",
        project_key="kanban",
        workspace_id=None,
        source_note_title=note.title,
        source_note_hash=note.content_hash,
        title=note.title,
        steps=steps,
    )


def _seed_database(tmp_path: Path):
    connection = connect_database(tmp_path / "state.sqlite3")
    note_one = upsert_note_from_loaded_note(
        connection,
        _note(
            title="Parser note",
            relative_path="Inbox/Parser note.md",
            transcript="Update the parser.",
        ),
    )
    note_two = upsert_note_from_loaded_note(
        connection,
        _note(
            title="Split note",
            relative_path="Inbox/Split note.md",
            transcript="Split the task into two steps.",
        ),
    )
    package_one = create_prompt_package(
        connection,
        note_one.id,
        _package(
            note_one,
            steps=[
                PromptStepV1(
                    step_index=1,
                    title="Update the parser",
                    prompt_markdown="Update the parser.",
                    external_task_key="obsidian:inbox/parser-note.md#step-1",
                )
            ],
        ),
    )
    package_two = create_prompt_package(
        connection,
        note_two.id,
        _package(
            note_two,
            steps=[
                PromptStepV1(
                    step_index=1,
                    title="Split the task",
                    prompt_markdown="Split the task into planner and execution work.",
                    external_task_key="obsidian:inbox/split-note.md#step-1",
                ),
                PromptStepV1(
                    step_index=2,
                    title="Add tests",
                    prompt_markdown="Add tests for the split plan.",
                    external_task_key="obsidian:inbox/split-note.md#step-2",
                    depends_on_step_indices=[1],
                ),
            ],
        ),
    )
    return connection, note_one, note_two, package_one, package_two


def _client(tmp_path: Path):
    calls = {"get_state": 0, "upsert": 0, "import": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        payload = None
        if request.content:
            payload = json.loads(request.content.decode("utf-8"))

        if request.url.path.endswith("/projects.list"):
            return httpx.Response(
                200,
                json={
                    "result": {
                        "data": {
                            "json": {
                                "projects": [
                                    {"id": "ws-1", "name": "Alpha", "path": "/alpha"},
                                    {"workspaceId": "ws-2", "title": "Beta", "rootPath": "/beta"},
                                ]
                            }
                        }
                    }
                },
            )
        if request.url.path.endswith("/workspace.getState"):
            calls["get_state"] += 1
            return httpx.Response(200, json={"result": {"data": {"json": {"canUpsertTaskByExternalKey": True}}}})
        if request.url.path.endswith("/workspace.upsertTaskByExternalKey"):
            calls["upsert"] += 1
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
        if request.url.path.endswith("/workspace.importTasks"):
            calls["import"] += 1
            if calls["import"] == 1:
                return httpx.Response(500, json={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "boom"}})
            return httpx.Response(
                200,
                json={
                    "result": {
                        "data": {
                            "json": {
                                "ok": True,
                                "mode": "import",
                                "task_count": len(payload["tasks"]),
                                "first_task": payload["tasks"][0]["prompt"],
                            }
                        }
                    }
                },
            )
        raise AssertionError(request.url.path)

    client = KanbanClient(
        KanbanClientConfig(base_url="http://kanban.local", workspace_id="ws-config"),
        transport=httpx.MockTransport(handler),
    )
    config = AppConfig(
        vault_path=Path(tmp_path),
        watch_folder="Inbox/Voice",
        processed_folder="Processed/Voice",
        database_path=tmp_path / "state.sqlite3",
        kanban_base_url="http://kanban.local",
        kanban_workspace_id="ws-config",
        template_dir=Path("/tmp/templates"),
    )
    return client, config, calls


def test_phase4_api_happy_path_review_preview_deliver_and_retry(tmp_path: Path) -> None:
    connection, note_one, note_two, package_one, package_two = _seed_database(tmp_path)
    client, config, calls = _client(tmp_path)
    app = create_app(config, db_connection=connection, kanban_client=client)

    with TestClient(app) as test_client:
        health = test_client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"ok": True, "service": "kanban-prompt-companion"}

        intake = test_client.get("/api/intake")
        assert intake.status_code == 200
        assert [item["title"] for item in intake.json()["items"]] == ["Split note", "Parser note"]

        intake_limited = test_client.get("/api/intake", params={"status": "parsed", "limit": 1})
        assert intake_limited.status_code == 200
        assert len(intake_limited.json()["items"]) == 1

        review = test_client.get("/api/review")
        assert review.status_code == 200
        assert {item["id"] for item in review.json()["items"]} == {package_one.id, package_two.id}

        step = package_one.steps[0]
        step_patch = test_client.patch(
            f"/api/steps/{step.id}",
            json={
                "title": "Update the parser, carefully",
                "prompt_markdown": "Update the parser and keep tests green.",
                "start_in_plan_mode": False,
            },
        )
        assert step_patch.status_code == 200
        assert step_patch.json()["step"]["title"] == "Update the parser, carefully"
        assert step_patch.json()["step"]["start_in_plan_mode"] is False

        forbidden_step_patch = test_client.patch(
            f"/api/steps/{step.id}",
            json={"external_task_key": "nope"},
        )
        assert forbidden_step_patch.status_code == 422

        approve = test_client.post(f"/api/packages/{package_one.id}/approve")
        assert approve.status_code == 200
        assert approve.json()["package"]["status"] == "approved"

        review_after_approve = test_client.get("/api/review")
        assert {item["id"] for item in review_after_approve.json()["items"]} == {package_two.id}

        preview_one = test_client.post(f"/api/packages/{package_one.id}/kanban/preview")
        assert preview_one.status_code == 200
        assert preview_one.json()["procedure"] == "workspace.upsertTaskByExternalKey"
        assert preview_one.json()["payload"]["title"] == "Update the parser, carefully"

        deliver_one = test_client.post(f"/api/packages/{package_one.id}/kanban/deliver")
        assert deliver_one.status_code == 200
        assert deliver_one.json()["delivery"]["status"] == "delivered"
        assert deliver_one.json()["kanban_response"]["mode"] == "upsert"

        package_one_detail = test_client.get(f"/api/packages/{package_one.id}")
        assert package_one_detail.json()["status"] == "delivered"

        preview_two = test_client.post(f"/api/packages/{package_two.id}/kanban/preview")
        assert preview_two.status_code == 200
        assert preview_two.json()["procedure"] == "workspace.importTasks"
        assert len(preview_two.json()["payload"]["tasks"]) == 2

        deliver_two = test_client.post(f"/api/packages/{package_two.id}/kanban/deliver")
        assert deliver_two.status_code == 200
        assert deliver_two.json()["delivery"]["status"] == "failed"
        assert "boom" in deliver_two.json()["delivery"]["error_message"]

        failed_delivery_id = deliver_two.json()["delivery"]["id"]
        failed_delivery_detail = test_client.get(f"/api/deliveries/{failed_delivery_id}")
        assert failed_delivery_detail.json()["delivery"]["status"] == "failed"

        step_two = package_two.steps[0]
        edited = test_client.patch(
            f"/api/steps/{step_two.id}",
            json={
                "prompt_markdown": "Split the work into parser cleanup and test coverage.",
            },
        )
        assert edited.status_code == 200
        assert "parser cleanup" in edited.json()["step"]["prompt_markdown"]

        retry = test_client.post(f"/api/deliveries/{failed_delivery_id}/retry")
        assert retry.status_code == 200
        assert retry.json()["delivery"]["status"] == "delivered"
        assert retry.json()["kanban_response"]["mode"] == "import"
        assert "parser cleanup" in retry.json()["kanban_response"]["first_task"]

        deliveries = test_client.get("/api/deliveries")
        assert {item["status"] for item in deliveries.json()["items"]} == {"delivered"}
        assert len(deliveries.json()["items"]) == 2

        note_detail = test_client.get(f"/api/intake/{note_two.id}")
        assert note_detail.status_code == 200
        assert note_detail.json()["package"]["status"] == "delivered"

        assert calls["import"] == 2
        assert get_note(connection, note_one.id).status == "delivered"
        assert get_note(connection, note_two.id).status == "delivered"
        assert len(list_deliveries(connection)) == 2


def test_phase4_workspace_discovery_and_guardrails(tmp_path: Path) -> None:
    connection, *_rest = _seed_database(tmp_path)
    client, config, _calls = _client(tmp_path)
    app = create_app(config, db_connection=connection, kanban_client=client)

    with TestClient(app) as test_client:
        workspaces = test_client.get("/api/kanban/workspaces")
        assert workspaces.status_code == 200
        assert workspaces.json()["items"] == [
            {"id": "ws-1", "name": "Alpha", "path": "/alpha"},
            {"id": "ws-2", "name": "Beta", "path": "/beta"},
        ]

        assert test_client.get("/api/rules").status_code == 404
        assert test_client.get("/api/templates").status_code == 404
