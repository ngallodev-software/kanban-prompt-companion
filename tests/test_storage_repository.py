from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.contracts import LoadedNote, PromptPackageV1, PromptStepV1
from app.ingest.dedupe import sha256_content_hash
from app.storage.db import connect_database
from app.storage.repository import (
    create_delivery_preview,
    create_prompt_package,
    get_delivery,
    get_prompt_package,
    list_deliveries,
    list_review_packages,
    mark_delivery_delivering,
    mark_delivery_failed,
    mark_delivery_success,
    mark_note_status,
    mark_package_approved,
    update_prompt_step_markdown,
    upsert_note_from_loaded_note,
)
from app.storage.schema import initialize_schema


def _loaded_note(*, title: str = "Voice Note", content: str = "First, update the parser.") -> LoadedNote:
    return LoadedNote(
        absolute_path="/vault/Inbox/Voice Note.md",
        relative_path="Inbox/Voice Note.md",
        title=title,
        frontmatter={"project": "kanban", "nested": {"one": 1}},
        body=content,
        control_text=None,
        transcript_text=content,
        content_hash=sha256_content_hash(content),
    )


def _package() -> PromptPackageV1:
    return PromptPackageV1(
        source_note_path="/vault/Inbox/Voice Note.md",
        cleaned_intent="Update the parser.",
        project_key="kanban",
        workspace_id="ws-1",
        source_note_title="Voice Note",
        source_note_hash="hash-1",
        title="Voice Note",
        steps=[
            PromptStepV1(
                step_index=1,
                title="Update the parser",
                external_task_key="obsidian:inbox/voice-note.md#step-1",
                prompt_markdown="Do the thing.",
            ),
            PromptStepV1(
                step_index=2,
                title="Add tests",
                external_task_key="obsidian:inbox/voice-note.md#step-2",
                prompt_markdown="Prove it works.",
                depends_on_step_indices=[1],
            ),
        ],
    )


def test_schema_initialization_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "state.sqlite3"
    connection = sqlite3.connect(database_path)
    try:
        initialize_schema(connection)
        initialize_schema(connection)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"notes", "prompt_packages", "prompt_steps", "deliveries"} <= tables
    finally:
        connection.close()


def test_upsert_note_updates_content_hash_by_relative_path(tmp_path: Path) -> None:
    connection = connect_database(tmp_path / "state.sqlite3")
    try:
        first = upsert_note_from_loaded_note(connection, _loaded_note(content="one"))
        second = upsert_note_from_loaded_note(connection, _loaded_note(content="two"))

        assert first.id == second.id
        assert second.content_hash == sha256_content_hash("two")
        assert second.frontmatter["nested"] == {"one": 1}
        assert second.status == "parsed"
    finally:
        connection.close()


def test_repository_happy_path_covers_packages_steps_deliveries(tmp_path: Path) -> None:
    connection = connect_database(tmp_path / "state.sqlite3")
    try:
        note = upsert_note_from_loaded_note(connection, _loaded_note())
        package = create_prompt_package(connection, note.id, _package())

        assert package.status == "review_ready"
        assert len(package.steps) == 2
        assert get_prompt_package(connection, package.id).steps[1].depends_on_step_indices == [1]

        updated_step = update_prompt_step_markdown(connection, package.steps[0].id, "Do the updated thing.")
        assert updated_step.prompt_markdown == "Do the updated thing."

        approved = mark_package_approved(connection, package.id)
        assert approved.status == "approved"
        assert approved.requires_review == 0

        preview_success = create_delivery_preview(
            connection,
            package.id,
            "ws-1",
            {"packageId": package.id, "tasks": 2},
        )
        assert preview_success.status == "previewed"
        assert preview_success.request == {"packageId": package.id, "tasks": 2}

        delivering = mark_delivery_delivering(connection, preview_success.id)
        assert delivering.status == "delivering"

        delivered = mark_delivery_success(connection, preview_success.id, response_payload={"ok": True})
        assert delivered.status == "delivered"
        assert delivered.response == {"ok": True}

        preview_failed = create_delivery_preview(
            connection,
            package.id,
            "ws-1",
            {"packageId": package.id, "tasks": 1},
        )
        failed = mark_delivery_failed(connection, preview_failed.id, error_message="boom")
        assert failed.status == "failed"
        assert failed.error_message == "boom"

        review_packages = list_review_packages(connection)
        assert review_packages == []
        assert {item.id for item in list_deliveries(connection)} == {preview_success.id, preview_failed.id}
        assert get_delivery(connection, preview_success.id).delivered_at is not None
        assert get_delivery(connection, preview_failed.id).delivered_at is None
    finally:
        connection.close()


def test_cascade_delete_from_package_to_steps_and_deliveries(tmp_path: Path) -> None:
    connection = connect_database(tmp_path / "state.sqlite3")
    try:
        note = upsert_note_from_loaded_note(connection, _loaded_note())
        package = create_prompt_package(connection, note.id, _package())
        create_delivery_preview(connection, package.id, "ws-1", {"packageId": package.id})

        connection.execute("DELETE FROM prompt_packages WHERE id = ?", (package.id,))
        connection.commit()

        assert connection.execute("SELECT COUNT(*) FROM prompt_steps").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0] == 0
    finally:
        connection.close()


def test_json_fields_round_trip(tmp_path: Path) -> None:
    connection = connect_database(tmp_path / "state.sqlite3")
    try:
        note = upsert_note_from_loaded_note(connection, _loaded_note())
        package = create_prompt_package(connection, note.id, _package())
        row = connection.execute("SELECT frontmatter_json FROM notes WHERE id = ?", (note.id,)).fetchone()
        assert json.loads(row[0])["nested"] == {"one": 1}
        step_row = connection.execute(
            "SELECT depends_on_step_indices_json FROM prompt_steps WHERE package_id = ? ORDER BY step_index",
            (package.id,),
        ).fetchall()
        assert json.loads(step_row[1][0]) == [1]
    finally:
        connection.close()
