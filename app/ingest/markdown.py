from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import frontmatter

from app.contracts import LoadedNote
from app.ingest.dedupe import sha256_content_hash


_HEADING_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)


def load_note(
    *,
    absolute_path: str | Path,
    relative_path: str,
    raw_text: str,
) -> LoadedNote | None:
    parsed = frontmatter.loads(raw_text)
    frontmatter_data = dict(parsed.metadata or {})
    status = frontmatter_data.get("status")
    if status is not None and str(status).strip().lower() != "new":
        return None

    watch_eligible = frontmatter_data.get("watch_eligible")
    if watch_eligible is False:
        return None
    if isinstance(watch_eligible, str) and watch_eligible.strip().lower() in {"false", "0", "no"}:
        return None

    body = parsed.content.strip()
    sections = _extract_sections(body)
    control_text = sections.get("control")
    transcript_text = sections.get("transcript") or body
    transcript_text = transcript_text.strip()
    if not transcript_text:
        return None

    title = str(frontmatter_data.get("title") or Path(absolute_path).stem).strip() or Path(absolute_path).stem

    return LoadedNote(
        absolute_path=str(Path(absolute_path).resolve()),
        relative_path=Path(relative_path).as_posix(),
        title=title,
        frontmatter=frontmatter_data,
        body=body,
        control_text=control_text,
        transcript_text=transcript_text,
        content_hash=sha256_content_hash(raw_text),
    )


def _extract_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in body.splitlines():
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            if current_key is not None:
                sections[current_key] = current_lines[:]
            current_key = heading_match.group("title").strip().lower()
            current_lines = []
            continue
        if current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        sections[current_key] = current_lines

    normalized: dict[str, str] = {}
    for key, lines in sections.items():
        normalized[key] = "\n".join(lines).strip()
    return normalized
