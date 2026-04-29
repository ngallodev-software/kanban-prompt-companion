from pathlib import Path

from app.ingest.paths import is_processable_markdown_path


def test_is_processable_markdown_path_accepts_normal_note(tmp_path: Path) -> None:
    note = tmp_path / "Inbox" / "Voice" / "Voice Note.md"
    note.parent.mkdir(parents=True)
    note.write_text("hi", encoding="utf-8")

    assert is_processable_markdown_path(note)


def test_is_processable_markdown_path_rejects_hidden_temp_and_non_md(tmp_path: Path) -> None:
    hidden = tmp_path / ".Hidden.md"
    temp = tmp_path / "Voice Note.swp"
    swap = tmp_path / "Voice Note.md.tmp"
    plain = tmp_path / "Voice Note.txt"
    folder = tmp_path / "Folder.md"

    hidden.write_text("hi", encoding="utf-8")
    temp.write_text("hi", encoding="utf-8")
    swap.write_text("hi", encoding="utf-8")
    plain.write_text("hi", encoding="utf-8")
    folder.mkdir()

    assert not is_processable_markdown_path(hidden)
    assert not is_processable_markdown_path(temp)
    assert not is_processable_markdown_path(swap)
    assert not is_processable_markdown_path(plain)
    assert not is_processable_markdown_path(folder)
