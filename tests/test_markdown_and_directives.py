from pathlib import Path

from app.contracts import LoadedNote
from app.ingest.dedupe import sha256_content_hash
from app.ingest.markdown import load_note
from app.pipeline.cleanup import cleanup_transcript
from app.pipeline.directives import parse_directives


def test_load_note_extracts_sections_and_title(tmp_path: Path) -> None:
    note_path = tmp_path / "Voice Note.md"
    raw = """---
title: Voice Title
status: new
watch_eligible: true
---

## Control
project is kanban

## Transcript
First, update the parser.
"""
    note_path.write_text(raw, encoding="utf-8")

    loaded = load_note(
        absolute_path=note_path,
        relative_path="Inbox/Voice Note.md",
        raw_text=raw,
    )

    assert loaded is not None
    assert loaded.title == "Voice Title"
    assert loaded.control_text == "project is kanban"
    assert loaded.transcript_text == "First, update the parser."
    assert loaded.body.startswith("## Control")
    assert loaded.content_hash == sha256_content_hash(raw)


def test_load_note_falls_back_to_body_and_skips_non_new_or_ineligible(tmp_path: Path) -> None:
    note_path = tmp_path / "Voice Note.md"
    fallback_raw = """---
---

Just do the thing.
"""
    skipped_status_raw = """---
status: done
---

## Transcript
Ignore me.
"""
    skipped_eligible_raw = """---
watch_eligible: false
---

## Transcript
Ignore me.
"""
    note_path.write_text(fallback_raw, encoding="utf-8")
    assert load_note(absolute_path=note_path, relative_path="Inbox/Voice Note.md", raw_text=fallback_raw) is not None
    assert load_note(absolute_path=note_path, relative_path="Inbox/Voice Note.md", raw_text=skipped_status_raw) is None
    assert load_note(absolute_path=note_path, relative_path="Inbox/Voice Note.md", raw_text=skipped_eligible_raw) is None


def test_parse_directives_reads_control_and_transcript_lines() -> None:
    directives = parse_directives(
        "project is kanban\nworkspace: ws-1\nbase ref is main\nchain: yes",
        "harness is codex\nprompt type is coding",
    )

    assert directives.project_key == "kanban"
    assert directives.workspace_id == "ws-1"
    assert directives.base_ref == "main"
    assert directives.harness == "codex"
    assert directives.prompt_type == "coding"
    assert directives.wants_chain is True


def test_cleanup_transcript_removes_fillers_preserves_code_and_collapses_false_starts() -> None:
    result = cleanup_transcript(
        "um I was going to I was going to update /tmp/file.md and run `pytest -q` like basically."
    )

    assert "um" not in result.cleaned_text
    assert "basically" not in result.cleaned_text
    assert "/tmp/file.md" in result.cleaned_text
    assert "`pytest -q`" in result.cleaned_text
    assert result.cleaned_text.count("I was going to") == 1
