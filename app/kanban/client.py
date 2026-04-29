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
        self._builtin_create_procedure: str | None = None

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

        try:
            return self.import_tasks(manifest, workspace_id=workspace_id)
        except KanbanClientError as exc:
            if not self._looks_like_missing_procedure_error(str(exc)):
                raise

        return self.create_tasks_with_builtin_trpc(manifest, workspace_id=workspace_id)

    def create_tasks_with_builtin_trpc(
        self,
        manifest: KanbanImportManifestV1,
        *,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        procedure = self._builtin_create_procedure or self._probe_builtin_create_procedure(workspace_id=workspace_id)
        created: list[dict[str, Any]] = []
        for task in manifest.tasks:
            created.append(self._create_single_task_builtin(task, procedure=procedure, workspace_id=workspace_id))
        return {
            "ok": True,
            "mode": "builtin_create",
            "procedure": procedure,
            "count": len(created),
            "created": created,
        }

    def _can_use_upsert(self, workspace_id: str | None) -> bool:
        if self._upsert_available is not None:
            return self._upsert_available
        return self.probe_upsert_capability(workspace_id)

    def _probe_builtin_create_procedure(self, workspace_id: str | None = None) -> str:
        state = self.get_workspace_state(workspace_id)
        available = state.get("availableMutations")
        candidates = [
            "workspace.createTask",
            "workspace.addTask",
            "tasks.create",
            "task.create",
            "workspace.create",
        ]
        if isinstance(available, dict):
            for candidate in candidates:
                if available.get(candidate):
                    self._builtin_create_procedure = candidate
                    return candidate
        self._builtin_create_procedure = "workspace.createTask"
        return self._builtin_create_procedure

    def _create_single_task_builtin(
        self,
        task: KanbanTaskV1,
        *,
        procedure: str,
        workspace_id: str | None,
    ) -> dict[str, Any]:
        body = {
            "title": task.title,
            "description": task.prompt,
            "externalTaskKey": task.external_task_key,
        }
        payload_candidates = [body, {"task": body}, {"input": body}]
        last_error: KanbanClientError | None = None
        for payload in payload_candidates:
            try:
                result = self._request(procedure, payload, workspace_id=workspace_id)
                if not isinstance(result, dict):
                    return {"result": result}
                return result
            except KanbanClientError as exc:
                last_error = exc
        raise KanbanClientError(str(last_error) if last_error else f"{procedure} failed")

    def _looks_like_missing_procedure_error(self, message: str) -> bool:
        text = message.lower()
        markers = [
            "not_found",
            "not found",
            "procedure not found",
            "no procedure",
            "cannot find procedure",
        ]
        return any(marker in text for marker in markers)

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
