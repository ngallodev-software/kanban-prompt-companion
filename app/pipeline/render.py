from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

from app.contracts import (
    PromptGuardrailsV1,
    PromptPackageV1,
    PromptStepV1,
    PromptVerificationV1,
)
from app.pipeline.cleanup import CleanupResult
from app.pipeline.directives import Directives


_STEP_MARKER_RE = re.compile(
    r"(?i)(?:(?:^|\n|\.\s+)(?:first|second|third|fourth|fifth|phase\s+\d+|step\s+(?:one|two|three|four|five|1|2|3|4|5)|then after that)\b)"
)


@dataclass(frozen=True)
class PackageBuildContext:
    source_note_path: str
    source_note_title: str
    source_note_hash: str
    relative_note_path: str


def build_prompt_package(
    *,
    note,
    directives: Directives,
    cleanup_result: CleanupResult,
    template_dir: str | Path,
    guardrails: PromptGuardrailsV1 | None = None,
    verification: PromptVerificationV1 | None = None,
) -> PromptPackageV1:
    cleaned_intent = cleanup_result.cleaned_text.strip()
    package = PromptPackageV1(
        source_note_path=note.absolute_path,
        source_note_title=note.title,
        source_note_hash=note.content_hash,
        title=note.title,
        cleaned_intent=cleaned_intent,
        project_key=directives.project_key or str(note.frontmatter.get("project") or "kanban"),
        workspace_id=directives.workspace_id or _string_or_none(note.frontmatter.get("workspace_id")),
        guardrails=guardrails or _guardrails_from_frontmatter(note.frontmatter),
        verification=verification or _verification_from_frontmatter(note.frontmatter),
        steps=[],
        cleanup_notes=list(cleanup_result.cleanup_notes),
        warnings=list(directives.warnings),
    )
    steps = _build_steps(package, directives, cleanup_result, note.relative_path, note.frontmatter)
    package = package.model_copy(update={"steps": steps})
    return render_prompt_package(package, template_dir=template_dir)


def render_prompt_package(
    package: PromptPackageV1,
    *,
    template_dir: str | Path,
    format_markdown: bool = False,
) -> PromptPackageV1:
    validated = PromptPackageV1.model_validate(package.model_dump())
    template = _load_template(Path(template_dir))
    rendered_steps: list[PromptStepV1] = []

    for step in validated.steps:
        if not step.step_intent.strip():
            raise ValueError(f"step {step.step_index} missing step_intent")
        rendered = template.render(
            package=validated.model_dump(),
            step=step.model_dump(),
            guardrail_items=list(validated.guardrails.items),
            verification_commands=list(validated.verification.commands),
            verification_notes=list(validated.verification.notes),
        )
        rendered = _normalize_markdown(rendered) if format_markdown else rendered.strip()
        rendered_steps.append(step.model_copy(update={"prompt_markdown": rendered}))

    return validated.model_copy(update={"steps": rendered_steps})


def _build_steps(
    package: PromptPackageV1,
    directives: Directives,
    cleanup_result: CleanupResult,
    relative_path: str,
    frontmatter: dict,
) -> list[PromptStepV1]:
    step_texts = _split_into_steps(cleanup_result.cleaned_text)
    steps: list[PromptStepV1] = []
    for index, step_text in enumerate(step_texts, start=1):
        depends = [index - 1] if index > 1 else []
        steps.append(
            PromptStepV1(
                step_index=index,
                title=_step_title(step_text, index),
                external_task_key=derive_external_task_key(relative_path, index),
                base_ref=directives.base_ref or _string_or_none(frontmatter.get("base_ref")),
                agent_id=directives.harness,
                start_in_plan_mode=True,
                depends_on_step_indices=depends,
                step_intent=step_text.strip(),
                cleanup_notes=list(cleanup_result.cleanup_notes),
                guardrails=package.guardrails,
                verification=package.verification,
            )
        )
    return steps


def derive_external_task_key(relative_note_path: str, step_index: int) -> str:
    normalized = Path(relative_note_path).as_posix().strip().lower()
    normalized = re.sub(r"[^a-z0-9._/-]+", "-", normalized)
    normalized = re.sub(r"/+", "/", normalized).strip("/")
    return f"obsidian:{normalized}#step-{step_index}"


def _split_into_steps(cleaned_intent: str) -> list[str]:
    text = cleaned_intent.strip()
    if not text:
        return [""]

    matches = list(_STEP_MARKER_RE.finditer(text))
    if len(matches) < 2:
        return [text]

    spans: list[tuple[int, int]] = []
    starts = [match.start() for match in matches]
    starts.append(len(text))
    for start, end in zip(starts, starts[1:]):
        segment = text[start:end].strip(" \n-:.,")
        if not segment:
            continue
        segment = _strip_step_prefix(segment)
        spans.append((start, end))
    if len(spans) < 2:
        return [text]

    results: list[str] = []
    for start, end in spans:
        segment = text[start:end].strip(" \n-:.,")
        segment = _strip_step_prefix(segment)
        if segment:
            results.append(segment)
    return results or [text]


def _strip_step_prefix(text: str) -> str:
    return re.sub(
        r"(?i)^(?:first|second|third|fourth|fifth|phase\s+\d+|step\s+(?:one|two|three|four|five|1|2|3|4|5)|then after that)\b[\s,:-]*",
        "",
        text.strip(),
        count=1,
    ).strip()


def _step_title(step_text: str, index: int) -> str:
    sentence = re.split(r"[.!?\n]", step_text.strip(), maxsplit=1)[0].strip()
    if not sentence:
        return f"Step {index}"
    words = sentence.split()
    title = " ".join(words[:10])
    return title[:80]


def _load_template(template_dir: Path):
    template_path = template_dir / "prompt_package.md.j2"
    if not template_path.exists():
        raise TemplateNotFound(str(template_path))
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env.get_template("prompt_package.md.j2")


def _normalize_markdown(text: str) -> str:
    normalized = text.strip()
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized


def _guardrails_from_frontmatter(frontmatter: dict) -> PromptGuardrailsV1:
    raw = frontmatter.get("guardrails")
    if isinstance(raw, list):
        return PromptGuardrailsV1(items=[str(item).strip() for item in raw if str(item).strip()])
    if isinstance(raw, str) and raw.strip():
        return PromptGuardrailsV1(items=[raw.strip()])
    return PromptGuardrailsV1()


def _verification_from_frontmatter(frontmatter: dict) -> PromptVerificationV1:
    raw = frontmatter.get("verification")
    if isinstance(raw, list):
        return PromptVerificationV1(commands=[str(item).strip() for item in raw if str(item).strip()])
    if isinstance(raw, str) and raw.strip():
        return PromptVerificationV1(commands=[raw.strip()])
    return PromptVerificationV1()


def _string_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
