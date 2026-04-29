from __future__ import annotations

import re

from pydantic import Field

from app.contracts import ContractModel


class CleanupResult(ContractModel):
    cleaned_text: str
    cleanup_notes: list[str] = Field(default_factory=list)


_FILLER_PATTERNS = [
    r"\b(?:um|uh|ah)\b",
    r"\b(?:you know|i mean|sort of|kind of|basically|actually)\b",
    r"\blike\b",
]
_FILLER_RE = re.compile("|".join(_FILLER_PATTERNS), re.I)
_REPEATED_PHRASE_RE = re.compile(r"\b(?P<phrase>[A-Za-z][A-Za-z']*(?:\s+[A-Za-z][A-Za-z']*){0,3})\b(?:\s*,?\s*)\b(?P=phrase)\b", re.I)
_WHITESPACE_RE = re.compile(r"[ \t]+")
_PUNCT_RE = re.compile(r"([!?\.])\1{1,}")
_FENCE_RE = re.compile(r"(^```.*?^```$)", re.M | re.S)


def cleanup_transcript(raw_text: str) -> CleanupResult:
    cleanup_notes: list[str] = []
    total_fillers_removed = 0
    total_false_starts = 0

    parts = _FENCE_RE.split(raw_text)
    cleaned_parts: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("```") and part.rstrip().endswith("```"):
            cleaned_parts.append(part)
            continue
        cleaned, filler_removed, false_starts = _cleanup_plain_text(part)
        total_fillers_removed += filler_removed
        total_false_starts += false_starts
        cleaned_parts.append(cleaned)

    cleaned_text = "".join(cleaned_parts)
    cleaned_text = _normalize_line_whitespace(cleaned_text)
    cleaned_text = _PUNCT_RE.sub(r"\1", cleaned_text)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()

    if total_fillers_removed:
        cleanup_notes.append(f"removed_fillers:{total_fillers_removed}")
    if total_false_starts:
        cleanup_notes.append(f"collapsed_false_starts:{total_false_starts}")
    if cleaned_text != raw_text.strip():
        cleanup_notes.append("normalized_whitespace")

    return CleanupResult(cleaned_text=cleaned_text, cleanup_notes=cleanup_notes)


def _cleanup_plain_text(text: str) -> tuple[str, int, int]:
    if not text.strip():
        return text, 0, 0

    lines = text.splitlines()
    cleaned_lines: list[str] = []
    filler_removed = 0
    false_starts = 0

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(">"):
            cleaned_lines.append(line)
            continue
        updated = _FILLER_RE.sub(lambda match: _replacement(match, counter=filler_removed), line)
        filler_removed += _count_filler_matches(line)
        collapsed, collapsed_count = _collapse_false_starts(updated)
        false_starts += collapsed_count
        cleaned_lines.append(collapsed)

    joined = "\n".join(cleaned_lines)
    joined = _WHITESPACE_RE.sub(" ", joined)
    joined = re.sub(r"\s+\n", "\n", joined)
    return joined, filler_removed, false_starts


def _replacement(match: re.Match[str], *, counter: int) -> str:
    text = match.group(0)
    return ""


def _count_filler_matches(text: str) -> int:
    return len(_FILLER_RE.findall(text))


def _collapse_false_starts(text: str) -> tuple[str, int]:
    collapsed = text
    count = 0
    while True:
        updated, replacements = _REPEATED_PHRASE_RE.subn(r"\g<phrase>", collapsed)
        if replacements == 0:
            return collapsed, count
        collapsed = updated
        count += replacements


def _normalize_line_whitespace(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines)
