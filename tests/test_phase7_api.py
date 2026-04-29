from __future__ import annotations

import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import AppConfig
from app.main import create_app
from app.storage import get_note

from tests.test_phase7_hardening import _kanban_client, _seed_database, _templates_dir


def test_api_flow_covers_intake_review_package_edit_preview_deliver_and_retry(tmp_path: Path) -> None:
    database, _note_path, _note, stored_note, package = _seed_database(tmp_path)
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
        intake = client.get("/api/intake")
        assert intake.status_code == 200
        assert intake.json()["items"][0]["id"] == stored_note.id

        review = client.get("/api/review")
        assert review.status_code == 200
        assert review.json()["items"][0]["id"] == package.id

        package_detail = client.get(f"/api/packages/{package.id}")
        assert package_detail.status_code == 200
        assert package_detail.json()["steps"][0]["external_task_key"].endswith("#step-1")

        step = package.steps[0]
        edit = client.patch(
            f"/api/steps/{step.id}",
            json={"title": "Parser cleanup", "prompt_markdown": "Rewrite the parser step with the updated constraint."},
        )
        assert edit.status_code == 200

        preview = client.post(f"/api/packages/{package.id}/kanban/preview")
        assert preview.status_code == 200
        assert preview.json()["procedure"] == "workspace.importTasks"
        assert preview.json()["payload"]["tasks"][0]["title"] == "Parser cleanup"

        deliver = client.post(f"/api/packages/{package.id}/kanban/deliver")
        assert deliver.status_code == 200
        assert deliver.json()["delivery"]["status"] == "failed"
        assert "temporary outage" in deliver.json()["delivery"]["error_message"]

        delivery_id = deliver.json()["delivery"]["id"]
        retry = client.post(f"/api/deliveries/{delivery_id}/retry")
        assert retry.status_code == 200
        assert retry.json()["delivery"]["status"] == "delivered"
        assert retry.json()["kanban_response"]["prompt"] == "Rewrite the parser step with the updated constraint."

        note_detail = client.get(f"/api/intake/{stored_note.id}")
        assert note_detail.status_code == 200
        assert note_detail.json()["package"]["status"] == "delivered"
        assert get_note(database, stored_note.id).status == "delivered"
