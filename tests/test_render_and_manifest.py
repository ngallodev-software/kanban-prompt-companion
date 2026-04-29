from pathlib import Path

from app.contracts import LoadedNote
from app.ingest.dedupe import sha256_content_hash
from app.pipeline.cleanup import CleanupResult
from app.pipeline.directives import Directives
from app.pipeline.render import build_prompt_package, derive_external_task_key, render_prompt_package
from app.kanban.manifest import build_kanban_manifest


def _note() -> LoadedNote:
    raw = "First, update the parser. Second, add tests."
    return LoadedNote(
        absolute_path="/vault/Inbox/Voice Note.md",
        relative_path="Inbox/Voice Note.md",
        title="Voice Note",
        frontmatter={"project": "kanban", "base_ref": "main"},
        body=raw,
        control_text=None,
        transcript_text=raw,
        content_hash=sha256_content_hash(raw),
    )


def _templates_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def test_build_prompt_package_renders_single_step_when_no_sequence(tmp_path: Path) -> None:
    note = _note().model_copy(update={"transcript_text": "Update the parser and add tests."})
    package = build_prompt_package(
        note=note,
        directives=Directives(project_key="kanban", workspace_id="ws-1", harness="codex", base_ref="main"),
        cleanup_result=CleanupResult(cleaned_text="Update the parser and add tests.", cleanup_notes=["normalized_whitespace"]),
        template_dir=_templates_dir(),
    )

    assert package.project_key == "kanban"
    assert package.workspace_id == "ws-1"
    assert len(package.steps) == 1
    assert package.steps[0].external_task_key == "obsidian:inbox/voice-note.md#step-1"
    assert "# Task" in package.steps[0].prompt_markdown
    assert "# Verification" in package.steps[0].prompt_markdown


def test_build_prompt_package_splits_explicit_sequence_and_builds_manifest() -> None:
    note = _note()
    package = build_prompt_package(
        note=note,
        directives=Directives(project_key="kanban", workspace_id="ws-1", harness="codex", base_ref="main"),
        cleanup_result=CleanupResult(
            cleaned_text="First update the parser. Second add tests.",
            cleanup_notes=["normalized_whitespace"],
        ),
        template_dir=_templates_dir(),
    )

    manifest = build_kanban_manifest(package)

    assert len(package.steps) == 2
    assert package.steps[1].depends_on_step_indices == [1]
    assert manifest.version == "v1"
    assert len(manifest.tasks) == 2
    assert len(manifest.links) == 1
    assert manifest.links[0].from_external_task_key == package.steps[0].external_task_key
    assert manifest.links[0].to_external_task_key == package.steps[1].external_task_key


def test_external_task_key_is_stable() -> None:
    assert derive_external_task_key("Inbox/Voice Note.md", 2) == derive_external_task_key("Inbox/Voice Note.md", 2)
