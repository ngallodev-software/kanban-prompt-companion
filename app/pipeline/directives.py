from __future__ import annotations

import re

from pydantic import Field

from app.contracts import ContractModel


class Directives(ContractModel):
    project_key: str | None = None
    workspace_id: str | None = None
    harness: str | None = None
    base_ref: str | None = None
    prompt_type: str | None = None
    wants_chain: bool = False
    warnings: list[str] = Field(default_factory=list)


_DIRECTIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(?:target\s+project|project)\s*(?:is|:)\s*(?P<value>.+)$", re.I), "project_key"),
    (re.compile(r"^(?:workspace)\s*(?:is|:)\s*(?P<value>.+)$", re.I), "workspace_id"),
    (re.compile(r"^(?:harness|agent)\s*(?:is|:)\s*(?P<value>.+)$", re.I), "harness"),
    (re.compile(r"^(?:base\s*ref|base)\s*(?:is|:)\s*(?P<value>.+)$", re.I), "base_ref"),
    (re.compile(r"^(?:prompt\s*type|prompt)\s*(?:is|:)\s*(?P<value>.+)$", re.I), "prompt_type"),
    (re.compile(r"^chain\s*(?:is|:)?\s*(?P<value>.+)$", re.I), "wants_chain"),
]


def parse_directives(*texts: str | None) -> Directives:
    directives = Directives()
    for text in texts:
        if not text:
            continue
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            matched = False
            for pattern, field_name in _DIRECTIVE_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                matched = True
                value = match.group("value").strip()
                if field_name == "wants_chain":
                    directives.wants_chain = _as_bool(value)
                    break
                current = getattr(directives, field_name)
                if current and current != value:
                    directives.warnings.append(f"conflict:{field_name}:{current}->{value}")
                setattr(directives, field_name, value)
                break
            if not matched:
                continue
    return directives


def _as_bool(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered in {"1", "true", "yes", "y", "on"}
