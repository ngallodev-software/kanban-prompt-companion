from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    ok: bool
    service: str = "kanban-prompt-companion"


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PromptGuardrailsV1(ContractModel):
    items: list[str] = Field(default_factory=list)


class PromptVerificationV1(ContractModel):
    commands: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PromptStepV1(ContractModel):
    step_index: int
    title: str
    prompt_markdown: str = ""
    external_task_key: str
    base_ref: str | None = None
    agent_id: str | None = None
    start_in_plan_mode: bool = True
    depends_on_step_indices: list[int] = Field(default_factory=list)
    step_intent: str = ""
    cleanup_notes: list[str] = Field(default_factory=list)
    guardrails: PromptGuardrailsV1 = Field(default_factory=PromptGuardrailsV1)
    verification: PromptVerificationV1 = Field(default_factory=PromptVerificationV1)


class PromptPackageV1(ContractModel):
    version: Literal["v1"] = "v1"
    source_note_path: str
    cleaned_intent: str
    project_key: str
    workspace_id: str | None = None
    source_note_title: str | None = None
    source_note_hash: str | None = None
    title: str | None = None
    steps: list[PromptStepV1]
    guardrails: PromptGuardrailsV1 = Field(default_factory=PromptGuardrailsV1)
    verification: PromptVerificationV1 = Field(default_factory=PromptVerificationV1)
    cleanup_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LoadedNote(ContractModel):
    absolute_path: str
    relative_path: str
    title: str
    frontmatter: dict[str, Any] = Field(default_factory=dict)
    body: str
    control_text: str | None = None
    transcript_text: str
    content_hash: str
