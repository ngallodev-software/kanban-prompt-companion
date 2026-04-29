from __future__ import annotations

import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import AppConfig
from app.ingest.markdown import load_note
from app.ingest.watcher import NoteWatcher
from app.kanban.client import KanbanClient, KanbanClientConfig
from app.kanban.manifest import build_kanban_manifest
from app.main import create_app
from app.pipeline.cleanup import cleanup_transcript
from app.pipeline.directives import parse_directives
from app.pipeline.render import build_prompt_package
from app.storage import create_prompt_package, get_delivery, get_note, list_deliveries, upsert_note_from_loaded_note
from app.storage.db import connect_database


def _fixture_path() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "parser_pipeline_voice_note.md"


def _fixture_text() -> str:
    return _fixture_path().read_text(encoding="utf-8")


def _vault_note_path(tmp_path: Path) -> Path:
    note_path = tmp_path / "Vault" / "Inbox" / "Voice" / "Parser pipeline voice note.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(_fixture_text(), encoding="utf-8")
    return note_path


def _templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def _loaded_note(note_path: Path):
    raw_text = note_path.read_text(encoding="utf-8")
    return load_note(
        absolute_path=note_path,
        relative_path="Inbox/Voice/Parser pipeline voice note.md",
        raw_text=raw_text,
    )


def _prompt_package(note):
    directives = parse_directives(note.control_text)
    cleanup = cleanup_transcript(note.transcript_text)
    return build_prompt_package(
        note=note,
        directives=directives,
        cleanup_result=cleanup,
        template_dir=_templates_dir(),
    )


def _seed_database(tmp_path: Path):
    database = connect_database(tmp_path / "state.sqlite3")
    note_path = _vault_note_path(tmp_path)
    note = _loaded_note(note_path)
    assert note is not None
    package = _prompt_package(note)
    stored_note = upsert_note_from_loaded_note(database, note)
    stored_package = create_prompt_package(database, stored_note.id, package)
    return database, note_path, note, stored_note, stored_package


def _kanban_client(handler) -> KanbanClient:
    return KanbanClient(
        KanbanClientConfig(base_url="http://kanban.local", workspace_id="kanban"),
        transport=httpx.MockTransport(handler),
    )


def test_watcher_startup_scan_discovers_fixture_note(tmp_path: Path) -> None:
    note_path = _vault_note_path(tmp_path)
    watcher = NoteWatcher(vault_path=tmp_path / "Vault", watch_folder="Inbox/Voice")

    assert watcher.startup_scan() == [note_path]


def test_watcher_ignores_symlink_escape_outside_watch_root(tmp_path: Path) -> None:
    note_path = _vault_note_path(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text(_fixture_text(), encoding="utf-8")
    escaped_link = note_path.parent / "escaped.md"
    escaped_link.symlink_to(outside)

    watcher = NoteWatcher(vault_path=tmp_path / "Vault", watch_folder="Inbox/Voice")

    discovered = watcher.startup_scan()
    assert note_path in discovered
    assert escaped_link not in discovered
    assert watcher.process_path(escaped_link) is None


def test_note_parser_extracts_frontmatter_control_and_transcript(tmp_path: Path) -> None:
    note_path = _vault_note_path(tmp_path)
    note = _loaded_note(note_path)

    assert note is not None
    assert note.title == "Parser pipeline voice note"
    assert note.frontmatter["status"] == "new"
    assert note.control_text == "project is kanban\nworkspace is kanban\nharness is codex\nbase ref is main"
    assert note.transcript_text.startswith("Um, I need you to add a simple parser")
    assert "Do not change unrelated Kanban files." in note.transcript_text


def test_cleanup_removes_fillers_but_preserves_technical_terms(tmp_path: Path) -> None:
    note = _loaded_note(_vault_note_path(tmp_path))
    assert note is not None

    result = cleanup_transcript(note.transcript_text)

    assert "Um" not in result.cleaned_text
    assert "uh" not in result.cleaned_text.lower()
    assert "front matter" in result.cleaned_text.lower()
    assert "transcript section" in result.cleaned_text.lower()
    assert "processed" in result.cleaned_text
    assert "Kanban" in result.cleaned_text
    assert "removed_fillers:2" in result.cleanup_notes


def test_prompt_package_generates_stable_external_task_key(tmp_path: Path) -> None:
    note = _loaded_note(_vault_note_path(tmp_path))
    assert note is not None

    package_a = _prompt_package(note)
    package_b = _prompt_package(note)

    assert package_a.steps[0].external_task_key == "obsidian:inbox/voice/parser-pipeline-voice-note.md#step-1"
    assert package_a.steps[0].external_task_key == package_b.steps[0].external_task_key
    assert "Do not change unrelated Kanban files." in package_a.steps[0].prompt_markdown


def test_kanban_manifest_preview_matches_expected_shape(tmp_path: Path) -> None:
    note = _loaded_note(_vault_note_path(tmp_path))
    assert note is not None

    package = _prompt_package(note)
    manifest = build_kanban_manifest(package)
    task = manifest.tasks[0].model_dump(by_alias=True, exclude_none=True)

    assert manifest.version == "v1"
    assert manifest.links == []
    assert task == {
        "externalTaskKey": "obsidian:inbox/voice/parser-pipeline-voice-note.md#step-1",
        "title": package.steps[0].title,
        "prompt": manifest.tasks[0].prompt,
        "baseRef": "main",
        "agentId": "codex",
        "startInPlanMode": True,
    }


def test_mocked_kanban_delivery_records_success(tmp_path: Path) -> None:
    database, _note_path, _note, stored_note, package = _seed_database(tmp_path)
    calls: list[tuple[str, object | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8")) if request.content else None
        calls.append((request.url.path, payload))
        if request.url.path.endswith("/workspace.getState"):
            return httpx.Response(200, json={"result": {"data": {"json": {}}}})
        if request.url.path.endswith("/workspace.importTasks"):
            return httpx.Response(200, json={"result": {"data": {"json": {"ok": True, "mode": "import"}}}})
        raise AssertionError(request.url.path)

    app = create_app(
        AppConfig(
            vault_path=tmp_path / "Vault",
            watch_folder="Inbox/Voice",
            processed_folder="Processed/Voice",
            database_path=tmp_path / "state.sqlite3",
            kanban_base_url="http://kanban.local",
            kanban_workspace_id="kanban",
            template_dir=_templates_dir(),
        ),
        db_connection=database,
        kanban_client=_kanban_client(handler),
    )

    with TestClient(app) as client:
        preview = client.post(f"/api/packages/{package.id}/kanban/preview")
        assert preview.status_code == 200
        assert preview.json()["procedure"] == "workspace.importTasks"

        deliver = client.post(f"/api/packages/{package.id}/kanban/deliver")
        assert deliver.status_code == 200
        assert deliver.json()["delivery"]["status"] == "delivered"
        assert deliver.json()["kanban_response"] == {"ok": True, "mode": "import"}
        assert get_note(database, stored_note.id).status == "delivered"
        assert get_delivery(database, deliver.json()["delivery"]["id"]).response == {"ok": True, "mode": "import"}
        assert calls[0][0].endswith("/workspace.getState")


def test_mocked_kanban_failure_records_useful_error(tmp_path: Path) -> None:
    database, _note_path, _note, _stored_note, package = _seed_database(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/workspace.getState"):
            return httpx.Response(200, json={"result": {"data": {"json": {}}}})
        if request.url.path.endswith("/workspace.importTasks"):
            return httpx.Response(
                500,
                json={"error": {"code": "BAD_REQUEST", "message": "missing workspace id"}},
            )
        raise AssertionError(request.url.path)

    app = create_app(
        AppConfig(
            vault_path=tmp_path / "Vault",
            watch_folder="Inbox/Voice",
            processed_folder="Processed/Voice",
            database_path=tmp_path / "state.sqlite3",
            kanban_base_url="http://kanban.local",
            kanban_workspace_id="kanban",
            template_dir=_templates_dir(),
        ),
        db_connection=database,
        kanban_client=_kanban_client(handler),
    )

    with TestClient(app) as client:
        deliver = client.post(f"/api/packages/{package.id}/kanban/deliver")
        assert deliver.status_code == 200
        assert deliver.json()["delivery"]["status"] == "failed"
        assert "workspace.importTasks failed" in deliver.json()["delivery"]["error_message"]
        assert "missing workspace id" in deliver.json()["delivery"]["error_message"]
        assert list_deliveries(database)[0].status == "failed"


def test_retry_uses_current_prompt_step_content(tmp_path: Path) -> None:
    database, _note_path, _note, _stored_note, package = _seed_database(tmp_path)
    state = {"imports": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/workspace.getState"):
            return httpx.Response(200, json={"result": {"data": {"json": {}}}})
        if request.url.path.endswith("/workspace.importTasks"):
            payload = json.loads(request.content.decode("utf-8"))
            state["imports"] += 1
            prompt = payload["tasks"][0]["prompt"]
            if state["imports"] == 1:
                return httpx.Response(
                    500,
                    json={"error": {"code": "FAILED_PRECONDITION", "message": "temporary outage"}},
                )
            return httpx.Response(200, json={"result": {"data": {"json": {"ok": True, "prompt": prompt}}}})
        raise AssertionError(request.url.path)

    app = create_app(
        AppConfig(
            vault_path=tmp_path / "Vault",
            watch_folder="Inbox/Voice",
            processed_folder="Processed/Voice",
            database_path=tmp_path / "state.sqlite3",
            kanban_base_url="http://kanban.local",
            kanban_workspace_id="kanban",
            template_dir=_templates_dir(),
        ),
        db_connection=database,
        kanban_client=_kanban_client(handler),
    )

    with TestClient(app) as client:
        failed = client.post(f"/api/packages/{package.id}/kanban/deliver")
        assert failed.status_code == 200
        assert failed.json()["delivery"]["status"] == "failed"

        step = package.steps[0]
        edit = client.patch(
            f"/api/steps/{step.id}",
            json={"prompt_markdown": "Rewrite the parser step with the updated constraint."},
        )
        assert edit.status_code == 200

        delivery_id = failed.json()["delivery"]["id"]
        retry = client.post(f"/api/deliveries/{delivery_id}/retry")
        assert retry.status_code == 200
        assert retry.json()["delivery"]["status"] == "delivered"
        assert retry.json()["kanban_response"]["prompt"] == "Rewrite the parser step with the updated constraint."
