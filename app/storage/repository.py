from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.contracts import LoadedNote, PromptPackageV1, PromptStepV1


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _json_value(text: str | None) -> Any:
    if text is None:
        return None
    return json.loads(text)


@dataclass(slots=True)
class NoteRecord:
    id: str
    absolute_path: str
    relative_path: str
    content_hash: str
    title: str
    frontmatter_json: str
    raw_body: str
    raw_transcript: str
    status: str
    watch_eligible: int
    discovered_at: str
    last_seen_at: str
    processed_at: str | None
    error_message: str | None

    @property
    def frontmatter(self) -> dict[str, Any]:
        return _json_value(self.frontmatter_json) or {}


@dataclass(slots=True)
class PromptStepRecord:
    id: str
    package_id: str
    step_index: int
    external_task_key: str
    title: str
    prompt_markdown: str
    base_ref: str | None
    agent_id: str | None
    start_in_plan_mode: int
    depends_on_step_indices_json: str
    status: str
    created_at: str
    updated_at: str

    @property
    def depends_on_step_indices(self) -> list[int]:
        return list(_json_value(self.depends_on_step_indices_json) or [])


@dataclass(slots=True)
class PromptPackageRecord:
    id: str
    note_id: str
    version: str
    cleaned_intent: str
    project_key: str | None
    kanban_workspace_id: str | None
    status: str
    requires_review: int
    created_at: str
    updated_at: str
    error_message: str | None
    steps: list[PromptStepRecord] = field(default_factory=list)


@dataclass(slots=True)
class DeliveryRecord:
    id: str
    package_id: str
    kanban_workspace_id: str
    request_json: str
    response_json: str | None
    status: str
    error_message: str | None
    created_at: str
    delivered_at: str | None

    @property
    def request(self) -> Any:
        return _json_value(self.request_json)

    @property
    def response(self) -> Any:
        return _json_value(self.response_json) if self.response_json is not None else None


def upsert_note_from_loaded_note(
    connection: sqlite3.Connection,
    note: LoadedNote,
    *,
    status: str = "parsed",
    watch_eligible: bool = True,
) -> NoteRecord:
    now = _utc_now()
    existing = connection.execute(
        "SELECT id, discovered_at FROM notes WHERE relative_path = ?",
        (note.relative_path,),
    ).fetchone()
    note_id = existing["id"] if existing else uuid.uuid4().hex
    discovered_at = existing["discovered_at"] if existing else now
    processed_at = now if status in {"parsed", "generated", "review_ready", "delivered", "failed"} else None
    connection.execute(
        """
        INSERT INTO notes (
            id, absolute_path, relative_path, content_hash, title, frontmatter_json,
            raw_body, raw_transcript, status, watch_eligible, discovered_at, last_seen_at,
            processed_at, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(relative_path) DO UPDATE SET
            absolute_path = excluded.absolute_path,
            content_hash = excluded.content_hash,
            title = excluded.title,
            frontmatter_json = excluded.frontmatter_json,
            raw_body = excluded.raw_body,
            raw_transcript = excluded.raw_transcript,
            status = excluded.status,
            watch_eligible = excluded.watch_eligible,
            last_seen_at = excluded.last_seen_at,
            processed_at = excluded.processed_at,
            error_message = excluded.error_message
        """,
        (
            note_id,
            note.absolute_path,
            note.relative_path,
            note.content_hash,
            note.title,
            _json_text(note.frontmatter),
            note.body,
            note.transcript_text,
            status,
            1 if watch_eligible else 0,
            discovered_at,
            now,
            processed_at,
            None,
        ),
    )
    connection.commit()
    return get_note_by_relative_path(connection, note.relative_path)


def mark_note_status(
    connection: sqlite3.Connection,
    note_id: str,
    status: str,
    *,
    processed_at: str | None = None,
    error_message: str | None = None,
) -> NoteRecord:
    now = processed_at or _utc_now()
    connection.execute(
        """
        UPDATE notes
        SET status = ?, processed_at = ?, error_message = ?
        WHERE id = ?
        """,
        (status, now, error_message, note_id),
    )
    connection.commit()
    return get_note(connection, note_id)


def update_note_location(
    connection: sqlite3.Connection,
    note_id: str,
    *,
    absolute_path: str,
    relative_path: str,
) -> NoteRecord:
    now = _utc_now()
    connection.execute(
        """
        UPDATE notes
        SET absolute_path = ?, relative_path = ?, last_seen_at = ?
        WHERE id = ?
        """,
        (absolute_path, relative_path, now, note_id),
    )
    connection.commit()
    return get_note(connection, note_id)


def create_prompt_package(
    connection: sqlite3.Connection,
    note_id: str,
    package: PromptPackageV1,
    *,
    status: str = "review_ready",
    requires_review: bool = True,
) -> PromptPackageRecord:
    now = _utc_now()
    package_id = uuid.uuid4().hex
    validated = PromptPackageV1.model_validate(package.model_dump())
    with connection:
        connection.execute(
            """
            INSERT INTO prompt_packages (
                id, note_id, version, cleaned_intent, project_key, kanban_workspace_id,
                status, requires_review, created_at, updated_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                package_id,
                note_id,
                validated.version,
                validated.cleaned_intent,
                validated.project_key,
                validated.workspace_id,
                status,
                1 if requires_review else 0,
                now,
                now,
                None,
            ),
        )
        for step in validated.steps:
            _insert_prompt_step(connection, package_id, step, now=now)
    return get_prompt_package(connection, package_id)


def get_prompt_package(connection: sqlite3.Connection, package_id: str) -> PromptPackageRecord:
    row = connection.execute(
        "SELECT * FROM prompt_packages WHERE id = ?",
        (package_id,),
    ).fetchone()
    if row is None:
        raise KeyError(package_id)
    steps = _load_prompt_steps(connection, package_id)
    return _package_from_row(row, steps=steps)


def list_review_packages(connection: sqlite3.Connection) -> list[PromptPackageRecord]:
    rows = connection.execute(
        """
        SELECT * FROM prompt_packages
        WHERE status = 'review_ready' OR requires_review = 1
        ORDER BY created_at ASC, id ASC
        """
    ).fetchall()
    return [_package_from_row(row, steps=_load_prompt_steps(connection, row["id"])) for row in rows]


def list_notes(
    connection: sqlite3.Connection,
    *,
    status: str | None = None,
    limit: int | None = None,
) -> list[NoteRecord]:
    query = "SELECT * FROM notes"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY discovered_at DESC, id DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    rows = connection.execute(query, params).fetchall()
    return [_note_from_row(row) for row in rows]


def get_latest_prompt_package_for_note(connection: sqlite3.Connection, note_id: str) -> PromptPackageRecord | None:
    row = connection.execute(
        """
        SELECT * FROM prompt_packages
        WHERE note_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (note_id,),
    ).fetchone()
    if row is None:
        return None
    return _package_from_row(row, steps=_load_prompt_steps(connection, row["id"]))


def update_prompt_step_markdown(
    connection: sqlite3.Connection,
    step_id: str,
    prompt_markdown: str,
) -> PromptStepRecord:
    now = _utc_now()
    connection.execute(
        """
        UPDATE prompt_steps
        SET prompt_markdown = ?, updated_at = ?
        WHERE id = ?
        """,
        (prompt_markdown, now, step_id),
    )
    connection.commit()
    row = connection.execute("SELECT * FROM prompt_steps WHERE id = ?", (step_id,)).fetchone()
    if row is None:
        raise KeyError(step_id)
    return _step_from_row(row)


def update_prompt_step(
    connection: sqlite3.Connection,
    step_id: str,
    *,
    title: str | None = None,
    prompt_markdown: str | None = None,
    base_ref: str | None = None,
    agent_id: str | None = None,
    start_in_plan_mode: bool | None = None,
) -> PromptStepRecord:
    current = connection.execute("SELECT * FROM prompt_steps WHERE id = ?", (step_id,)).fetchone()
    if current is None:
        raise KeyError(step_id)

    assignments: list[str] = []
    params: list[Any] = []
    now = _utc_now()

    if title is not None:
        assignments.append("title = ?")
        params.append(title)
    if prompt_markdown is not None:
        assignments.append("prompt_markdown = ?")
        params.append(prompt_markdown)
    if base_ref is not None:
        assignments.append("base_ref = ?")
        params.append(base_ref)
    if agent_id is not None:
        assignments.append("agent_id = ?")
        params.append(agent_id)
    if start_in_plan_mode is not None:
        assignments.append("start_in_plan_mode = ?")
        params.append(1 if start_in_plan_mode else 0)

    assignments.append("updated_at = ?")
    params.append(now)
    params.append(step_id)

    if assignments:
        connection.execute(
            f"""
            UPDATE prompt_steps
            SET {", ".join(assignments)}
            WHERE id = ?
            """,
            params,
        )
        connection.commit()
    row = connection.execute("SELECT * FROM prompt_steps WHERE id = ?", (step_id,)).fetchone()
    if row is None:
        raise KeyError(step_id)
    return _step_from_row(row)


def mark_package_approved(connection: sqlite3.Connection, package_id: str) -> PromptPackageRecord:
    now = _utc_now()
    connection.execute(
        """
        UPDATE prompt_packages
        SET status = 'approved', requires_review = 0, updated_at = ?
        WHERE id = ?
        """,
        (now, package_id),
    )
    connection.commit()
    return get_prompt_package(connection, package_id)


def mark_prompt_package_status(
    connection: sqlite3.Connection,
    package_id: str,
    *,
    status: str,
    requires_review: bool | None = None,
    error_message: str | None = None,
) -> PromptPackageRecord:
    now = _utc_now()
    assignments = ["status = ?", "updated_at = ?", "error_message = ?"]
    params: list[Any] = [status, now, error_message]
    if requires_review is not None:
        assignments.append("requires_review = ?")
        params.append(1 if requires_review else 0)
    params.append(package_id)
    connection.execute(
        f"""
        UPDATE prompt_packages
        SET {", ".join(assignments)}
        WHERE id = ?
        """,
        params,
    )
    connection.commit()
    return get_prompt_package(connection, package_id)


def update_prompt_package_workspace(
    connection: sqlite3.Connection,
    package_id: str,
    workspace_id: str | None,
) -> PromptPackageRecord:
    now = _utc_now()
    normalized_workspace_id = str(workspace_id).strip() if workspace_id is not None else None
    if normalized_workspace_id == "":
        normalized_workspace_id = None
    connection.execute(
        """
        UPDATE prompt_packages
        SET kanban_workspace_id = ?, updated_at = ?
        WHERE id = ?
        """,
        (normalized_workspace_id, now, package_id),
    )
    connection.commit()
    return get_prompt_package(connection, package_id)


def mark_prompt_steps_status(
    connection: sqlite3.Connection,
    package_id: str,
    *,
    status: str,
) -> list[PromptStepRecord]:
    now = _utc_now()
    connection.execute(
        """
        UPDATE prompt_steps
        SET status = ?, updated_at = ?
        WHERE package_id = ?
        """,
        (status, now, package_id),
    )
    connection.commit()
    return _load_prompt_steps(connection, package_id)


def create_delivery_preview(
    connection: sqlite3.Connection,
    package_id: str,
    kanban_workspace_id: str,
    request_payload: Any,
    *,
    response_payload: Any | None = None,
    status: str = "previewed",
) -> DeliveryRecord:
    now = _utc_now()
    delivery_id = uuid.uuid4().hex
    connection.execute(
        """
        INSERT INTO deliveries (
            id, package_id, kanban_workspace_id, request_json, response_json,
            status, error_message, created_at, delivered_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            delivery_id,
            package_id,
            kanban_workspace_id,
            _json_text(request_payload),
            _json_text(response_payload) if response_payload is not None else None,
            status,
            None,
            now,
            None,
        ),
    )
    connection.commit()
    return get_delivery(connection, delivery_id)


def update_delivery_request(
    connection: sqlite3.Connection,
    delivery_id: str,
    request_payload: Any,
    *,
    kanban_workspace_id: str | None = None,
) -> DeliveryRecord:
    now = _utc_now()
    assignments = ["request_json = ?", "created_at = ?"]
    params: list[Any] = [_json_text(request_payload), now]
    if kanban_workspace_id is not None:
        assignments.append("kanban_workspace_id = ?")
        params.append(kanban_workspace_id)
    params.append(delivery_id)
    connection.execute(
        f"""
        UPDATE deliveries
        SET {", ".join(assignments)}
        WHERE id = ?
        """,
        params,
    )
    connection.commit()
    return get_delivery(connection, delivery_id)


def mark_delivery_delivering(connection: sqlite3.Connection, delivery_id: str) -> DeliveryRecord:
    connection.execute(
        """
        UPDATE deliveries
        SET status = 'delivering'
        WHERE id = ?
        """,
        (delivery_id,),
    )
    connection.commit()
    return get_delivery(connection, delivery_id)


def mark_delivery_success(
    connection: sqlite3.Connection,
    delivery_id: str,
    *,
    response_payload: Any | None = None,
) -> DeliveryRecord:
    now = _utc_now()
    connection.execute(
        """
        UPDATE deliveries
        SET status = 'delivered', response_json = COALESCE(?, response_json),
            error_message = NULL, delivered_at = ?
        WHERE id = ?
        """,
        (_json_text(response_payload) if response_payload is not None else None, now, delivery_id),
    )
    connection.commit()
    return get_delivery(connection, delivery_id)


def mark_delivery_failed(
    connection: sqlite3.Connection,
    delivery_id: str,
    *,
    error_message: str,
    response_payload: Any | None = None,
    status: str = "failed",
) -> DeliveryRecord:
    connection.execute(
        """
        UPDATE deliveries
        SET status = ?, response_json = COALESCE(?, response_json), error_message = ?,
            delivered_at = NULL
        WHERE id = ?
        """,
        (status, _json_text(response_payload) if response_payload is not None else None, error_message, delivery_id),
    )
    connection.commit()
    return get_delivery(connection, delivery_id)


def list_deliveries(connection: sqlite3.Connection) -> list[DeliveryRecord]:
    rows = connection.execute(
        "SELECT * FROM deliveries ORDER BY created_at ASC, id ASC"
    ).fetchall()
    return [_delivery_from_row(row) for row in rows]


def get_delivery(connection: sqlite3.Connection, delivery_id: str) -> DeliveryRecord:
    row = connection.execute("SELECT * FROM deliveries WHERE id = ?", (delivery_id,)).fetchone()
    if row is None:
        raise KeyError(delivery_id)
    return _delivery_from_row(row)


def get_note(connection: sqlite3.Connection, note_id: str) -> NoteRecord:
    row = connection.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        raise KeyError(note_id)
    return _note_from_row(row)


def get_note_by_relative_path(connection: sqlite3.Connection, relative_path: str) -> NoteRecord:
    row = connection.execute("SELECT * FROM notes WHERE relative_path = ?", (relative_path,)).fetchone()
    if row is None:
        raise KeyError(relative_path)
    return _note_from_row(row)


def _insert_prompt_step(connection: sqlite3.Connection, package_id: str, step: PromptStepV1, *, now: str) -> None:
    connection.execute(
        """
        INSERT INTO prompt_steps (
            id, package_id, step_index, external_task_key, title, prompt_markdown,
            base_ref, agent_id, start_in_plan_mode, depends_on_step_indices_json,
            status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            uuid.uuid4().hex,
            package_id,
            step.step_index,
            step.external_task_key,
            step.title,
            step.prompt_markdown,
            step.base_ref,
            step.agent_id,
            1 if step.start_in_plan_mode else 0,
            _json_text(step.depends_on_step_indices),
            "draft",
            now,
            now,
        ),
    )


def _load_prompt_steps(connection: sqlite3.Connection, package_id: str) -> list[PromptStepRecord]:
    rows = connection.execute(
        """
        SELECT * FROM prompt_steps
        WHERE package_id = ?
        ORDER BY step_index ASC
        """,
        (package_id,),
    ).fetchall()
    return [_step_from_row(row) for row in rows]


def _note_from_row(row: sqlite3.Row) -> NoteRecord:
    return NoteRecord(
        id=row["id"],
        absolute_path=row["absolute_path"],
        relative_path=row["relative_path"],
        content_hash=row["content_hash"],
        title=row["title"],
        frontmatter_json=row["frontmatter_json"],
        raw_body=row["raw_body"],
        raw_transcript=row["raw_transcript"],
        status=row["status"],
        watch_eligible=row["watch_eligible"],
        discovered_at=row["discovered_at"],
        last_seen_at=row["last_seen_at"],
        processed_at=row["processed_at"],
        error_message=row["error_message"],
    )


def _package_from_row(row: sqlite3.Row, *, steps: list[PromptStepRecord]) -> PromptPackageRecord:
    return PromptPackageRecord(
        id=row["id"],
        note_id=row["note_id"],
        version=row["version"],
        cleaned_intent=row["cleaned_intent"],
        project_key=row["project_key"],
        kanban_workspace_id=row["kanban_workspace_id"],
        status=row["status"],
        requires_review=row["requires_review"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        error_message=row["error_message"],
        steps=steps,
    )


def _step_from_row(row: sqlite3.Row) -> PromptStepRecord:
    return PromptStepRecord(
        id=row["id"],
        package_id=row["package_id"],
        step_index=row["step_index"],
        external_task_key=row["external_task_key"],
        title=row["title"],
        prompt_markdown=row["prompt_markdown"],
        base_ref=row["base_ref"],
        agent_id=row["agent_id"],
        start_in_plan_mode=row["start_in_plan_mode"],
        depends_on_step_indices_json=row["depends_on_step_indices_json"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _delivery_from_row(row: sqlite3.Row) -> DeliveryRecord:
    return DeliveryRecord(
        id=row["id"],
        package_id=row["package_id"],
        kanban_workspace_id=row["kanban_workspace_id"],
        request_json=row["request_json"],
        response_json=row["response_json"],
        status=row["status"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        delivered_at=row["delivered_at"],
    )
