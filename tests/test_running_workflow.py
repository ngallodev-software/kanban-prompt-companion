from __future__ import annotations

import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import AppConfig
from app.ingest.watcher import NoteWatcher
from app.kanban.client import KanbanClient, KanbanClientConfig
from app.main import create_app
from app.pipeline.cleanup import cleanup_transcript
from app.pipeline.directives import parse_directives
from app.pipeline.render import build_prompt_package
from app.storage import create_prompt_package, get_note, upsert_note_from_loaded_note
from app.storage.db import connect_database


def _templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def _fixture_text() -> str:
    return (Path(__file__).resolve().parent / "fixtures" / "parser_pipeline_voice_note.md").read_text(
        encoding="utf-8"
    )


def test_running_workflow_processes_a_real_note_file_and_delivers_it(tmp_path: Path) -> None:
    vault_path = tmp_path / "Vault"
    note_path = vault_path / "Inbox" / "Voice" / "Parser pipeline voice note.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(_fixture_text(), encoding="utf-8")

    watcher = NoteWatcher(vault_path=vault_path, watch_folder="Inbox/Voice")
    assert watcher.startup_scan() == [note_path]

    note = watcher.process_path(note_path)
    assert note is not None
    assert note.title == "Parser pipeline voice note"
    assert "Do not change unrelated Kanban files." in note.transcript_text

    connection = connect_database(tmp_path / "state.sqlite3")
    stored_note = upsert_note_from_loaded_note(connection, note)
    assert stored_note.status == "parsed"

    directives = parse_directives(note.control_text)
    cleanup_result = cleanup_transcript(note.transcript_text)
    package = build_prompt_package(
        note=note,
        directives=directives,
        cleanup_result=cleanup_result,
        template_dir=_templates_dir(),
    )
    stored_package = create_prompt_package(connection, stored_note.id, package)

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
            watch_folder="Inbox/Voice",
            processed_folder="Processed/Voice",
            database_path=tmp_path / "state.sqlite3",
            kanban_base_url="http://kanban.local",
            kanban_workspace_id="kanban",
            template_dir=_templates_dir(),
        ),
        db_connection=connection,
        kanban_client=KanbanClient(
            KanbanClientConfig(base_url="http://kanban.local", workspace_id="kanban"),
            transport=httpx.MockTransport(handler),
        ),
    )

    with TestClient(app) as client:
        intake = client.get("/api/intake")
        assert intake.status_code == 200
        assert intake.json()["items"][0]["id"] == stored_note.id

        review = client.get("/api/review")
        assert review.status_code == 200
        assert review.json()["items"][0]["id"] == stored_package.id

        note_detail = client.get(f"/api/intake/{stored_note.id}")
        assert note_detail.status_code == 200
        assert note_detail.json()["package"]["id"] == stored_package.id
        assert note_detail.json()["cleaned_intent"]

        preview = client.post(f"/api/packages/{stored_package.id}/kanban/preview")
        assert preview.status_code == 200
        assert preview.json()["procedure"] == "workspace.upsertTaskByExternalKey"
        assert preview.json()["payload"]["title"] == package.steps[0].title

        deliver = client.post(f"/api/packages/{stored_package.id}/kanban/deliver")
        assert deliver.status_code == 200
        assert deliver.json()["delivery"]["status"] == "delivered"
        assert deliver.json()["kanban_response"]["mode"] == "upsert"
        assert get_note(connection, stored_note.id).status == "delivered"
        assert calls == [
            "/api/trpc/workspace.getState",
            "/api/trpc/workspace.getState",
            "/api/trpc/workspace.upsertTaskByExternalKey",
        ]
