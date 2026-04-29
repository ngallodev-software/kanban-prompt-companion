from collections import defaultdict

import httpx
import pytest

from app.kanban.client import KanbanClient, KanbanClientConfig, KanbanClientError
from app.kanban.manifest import KanbanImportManifestV1, KanbanTaskV1


def _json_response(data: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json=data)


def test_list_projects_and_add_project() -> None:
    calls = defaultdict(int)

    def handler(request: httpx.Request) -> httpx.Response:
        calls[request.url.path] += 1
        if request.url.path.endswith("/projects.list"):
            assert request.headers["x-kanban-passcode"] == "pass-1"
            return _json_response({"result": {"data": {"json": {"currentProjectId": "p1", "projects": [{"id": "p1", "name": "Alpha", "path": "/vault/alpha"}]}}}})
        if request.url.path.endswith("/projects.add"):
            assert request.content
            return _json_response({"result": {"data": {"json": {"id": "p2"}}}})
        raise AssertionError(request.url.path)

    client = KanbanClient(
        KanbanClientConfig(base_url="http://kanban.local", workspace_id="ws-1", passcode="pass-1"),
        transport=httpx.MockTransport(handler),
    )

    assert client.list_projects() == [{"id": "p1", "name": "Alpha", "path": "/vault/alpha"}]
    assert client.add_project("/vault/kanban") == {"id": "p2"}
    assert calls["/api/trpc/projects.list"] == 1
    assert calls["/api/trpc/projects.add"] == 1


def test_import_or_upsert_prefers_upsert_when_available() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/workspace.getState"):
            return _json_response({"result": {"data": {"json": {"canUpsertTaskByExternalKey": True}}}})
        if request.url.path.endswith("/workspace.upsertTaskByExternalKey"):
            return _json_response({"result": {"data": {"json": {"ok": True, "mode": "upsert"}}}})
        raise AssertionError(request.url.path)

    client = KanbanClient(
        KanbanClientConfig(base_url="http://kanban.local", workspace_id="ws-1"),
        transport=httpx.MockTransport(handler),
    )
    manifest = KanbanImportManifestV1(
        tasks=[
            KanbanTaskV1(
                externalTaskKey="obsidian:inbox/voice note.md#step-1",
                title="Step 1",
                prompt="Do the thing",
            )
        ]
    )

    assert client.import_or_upsert(manifest) == {"ok": True, "mode": "upsert"}
    assert calls == ["/api/trpc/workspace.getState", "/api/trpc/workspace.upsertTaskByExternalKey"]


def test_import_or_upsert_falls_back_to_import_when_upsert_unavailable() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/workspace.getState"):
            return _json_response({"result": {"data": {"json": {"canImportTasks": True}}}})
        if request.url.path.endswith("/workspace.importTasks"):
            return _json_response({"result": {"data": {"json": {"ok": True, "mode": "import"}}}})
        raise AssertionError(request.url.path)

    client = KanbanClient(
        KanbanClientConfig(base_url="http://kanban.local", workspace_id="ws-1"),
        transport=httpx.MockTransport(handler),
    )
    manifest = KanbanImportManifestV1(
        tasks=[
            KanbanTaskV1(
                externalTaskKey="obsidian:inbox/voice note.md#step-1",
                title="Step 1",
                prompt="Do the thing",
            )
        ]
    )

    assert client.import_or_upsert(manifest) == {"ok": True, "mode": "import"}
    assert calls == ["/api/trpc/workspace.getState", "/api/trpc/workspace.importTasks"]


def test_import_or_upsert_falls_back_to_builtin_create_when_import_unavailable() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/workspace.getState"):
            return _json_response(
                {
                    "result": {
                        "data": {
                            "json": {
                                "availableMutations": {
                                    "workspace.createTask": True,
                                }
                            }
                        }
                    }
                }
            )
        if request.url.path.endswith("/workspace.importTasks"):
            return _json_response({"error": {"code": "NOT_FOUND", "message": "procedure not found"}}, status_code=404)
        if request.url.path.endswith("/workspace.createTask"):
            return _json_response({"result": {"data": {"json": {"ok": True, "id": "task-1"}}}})
        raise AssertionError(request.url.path)

    client = KanbanClient(
        KanbanClientConfig(base_url="http://kanban.local", workspace_id="ws-1"),
        transport=httpx.MockTransport(handler),
    )
    manifest = KanbanImportManifestV1(
        tasks=[
            KanbanTaskV1(
                externalTaskKey="obsidian:inbox/voice note.md#step-1",
                title="Step 1",
                prompt="Do the thing",
            )
        ]
    )

    assert client.import_or_upsert(manifest) == {
        "ok": True,
        "mode": "builtin_create",
        "procedure": "workspace.createTask",
        "count": 1,
        "created": [{"ok": True, "id": "task-1"}],
    }
    assert calls == [
        "/api/trpc/workspace.getState",
        "/api/trpc/workspace.importTasks",
        "/api/trpc/workspace.getState",
        "/api/trpc/workspace.createTask",
    ]


def test_failed_kanban_response_raises_clear_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/workspace.importTasks"):
            return _json_response({"error": "boom"}, status_code=500)
        return _json_response({"result": {"data": {"json": {"canUpsertTaskByExternalKey": False}}}})

    client = KanbanClient(
        KanbanClientConfig(base_url="http://kanban.local", workspace_id="ws-1"),
        transport=httpx.MockTransport(handler),
    )
    manifest = KanbanImportManifestV1(
        tasks=[
            KanbanTaskV1(
                externalTaskKey="obsidian:inbox/voice note.md#step-1",
                title="Step 1",
                prompt="Do the thing",
            )
        ]
    )

    with pytest.raises(KanbanClientError):
        client.import_tasks(manifest)
