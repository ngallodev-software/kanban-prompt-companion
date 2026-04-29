from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.kanban.manifest import KanbanImportManifestV1, KanbanTaskV1


class KanbanClientError(RuntimeError):
    pass


class KanbanTransportError(KanbanClientError):
    pass


@dataclass
class KanbanClientConfig:
    base_url: str
    workspace_id: str | None = None
    passcode: str | None = None
    timeout_seconds: float = 20.0


class KanbanClient:
    def __init__(
        self,
        config: KanbanClientConfig,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config
        self._transport = transport
        self._upsert_available: bool | None = None

    def list_projects(self) -> list[dict[str, Any]]:
        payload = self._request("projects.list")
        projects = payload.get("projects", []) if isinstance(payload, dict) else []
        return list(projects)

    def add_project(self, path: str) -> dict[str, Any]:
        payload = self._request("projects.add", {"path": path})
        if not isinstance(payload, dict):
            raise KanbanClientError("invalid projects.add response")
        return payload

    def get_workspace_state(self, workspace_id: str | None = None) -> dict[str, Any]:
        payload = self._request("workspace.getState", workspace_id=workspace_id)
        if not isinstance(payload, dict):
            raise KanbanClientError("invalid workspace.getState response")
        return payload

    def probe_upsert_capability(self, workspace_id: str | None = None) -> bool:
        state = self.get_workspace_state(workspace_id)
        capability_flags = [
            state.get("canUpsertTaskByExternalKey"),
            (state.get("capabilities") or {}).get("upsertTaskByExternalKey") if isinstance(state.get("capabilities"), dict) else None,
            (state.get("availableMutations") or {}).get("workspace.upsertTaskByExternalKey")
            if isinstance(state.get("availableMutations"), dict)
            else None,
        ]
        self._upsert_available = any(bool(flag) for flag in capability_flags)
        return bool(self._upsert_available)

    def import_tasks(self, manifest: KanbanImportManifestV1, workspace_id: str | None = None) -> dict[str, Any]:
        payload = self._request(
            "workspace.importTasks",
            manifest.model_dump(by_alias=True, exclude_none=True),
            workspace_id=workspace_id,
        )
        if not isinstance(payload, dict):
            raise KanbanClientError("invalid workspace.importTasks response")
        return payload

    def upsert_task_by_external_key(
        self,
        task: KanbanTaskV1,
        *,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        payload = self._request(
            "workspace.upsertTaskByExternalKey",
            task.model_dump(by_alias=True, exclude_none=True),
            workspace_id=workspace_id,
        )
        if not isinstance(payload, dict):
            raise KanbanClientError("invalid workspace.upsertTaskByExternalKey response")
        self._upsert_available = True
        return payload

    def import_or_upsert(self, manifest: KanbanImportManifestV1, workspace_id: str | None = None) -> dict[str, Any]:
        if len(manifest.tasks) == 1 and self._can_use_upsert(workspace_id):
            try:
                return self.upsert_task_by_external_key(manifest.tasks[0], workspace_id=workspace_id)
            except KanbanClientError:
                self._upsert_available = False
        return self.import_tasks(manifest, workspace_id=workspace_id)

    def _can_use_upsert(self, workspace_id: str | None) -> bool:
        if self._upsert_available is not None:
            return self._upsert_available
        return self.probe_upsert_capability(workspace_id)

    def _request(
        self,
        procedure: str,
        payload: object | None = None,
        *,
        workspace_id: str | None = None,
    ) -> Any:
        headers = {"content-type": "application/json"}
        resolved_workspace_id = workspace_id or self.config.workspace_id
        if resolved_workspace_id:
            headers["x-kanban-workspace-id"] = resolved_workspace_id

        try:
            with httpx.Client(
                base_url=self.config.base_url.rstrip("/"),
                timeout=self.config.timeout_seconds,
                transport=self._transport,
            ) as client:
                response = client.post(f"/api/trpc/{procedure}", json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise KanbanTransportError(str(exc)) from exc

        data = self._unwrap(response)
        if response.status_code >= 400:
            raise KanbanClientError(self._format_error(procedure, response.status_code, data))
        return data

    def _unwrap(self, response: httpx.Response) -> Any:
        try:
            payload = response.json()
        except ValueError as exc:
            raise KanbanClientError("invalid json response") from exc

        if isinstance(payload, list) and payload:
            payload = payload[0]
        if isinstance(payload, dict):
            result = payload.get("result")
            if isinstance(result, dict):
                data = result.get("data")
                if isinstance(data, dict) and "json" in data:
                    return data["json"]
                return data
            if "error" in payload:
                return payload["error"]
        return payload

    def _format_error(self, procedure: str, status_code: int, data: Any) -> str:
        if isinstance(data, dict):
            code = data.get("code") or data.get("errorCode") or data.get("type")
            message = data.get("message") or data.get("error") or data.get("detail")
            if isinstance(message, dict):
                message = message.get("message") or message.get("detail") or message
            if code and message:
                return f"{procedure} failed: {status_code}: {code}: {message}"
            if message:
                return f"{procedure} failed: {status_code}: {message}"
            if code:
                return f"{procedure} failed: {status_code}: {code}"
        return f"{procedure} failed: {status_code}: {data}"
