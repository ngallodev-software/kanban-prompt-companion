from __future__ import annotations

from typing import Any, Literal

from pydantic import ConfigDict, Field

from app.contracts import ContractModel, PromptPackageV1


class KanbanTaskV1(ContractModel):
    model_config = ConfigDict(populate_by_name=True)

    external_task_key: str = Field(alias="externalTaskKey")
    title: str
    prompt: str
    base_ref: str | None = Field(default=None, alias="baseRef")
    agent_id: str | None = Field(default=None, alias="agentId")
    start_in_plan_mode: bool = Field(default=True, alias="startInPlanMode")


class KanbanLinkV1(ContractModel):
    model_config = ConfigDict(populate_by_name=True)

    from_external_task_key: str = Field(alias="fromExternalTaskKey")
    to_external_task_key: str = Field(alias="toExternalTaskKey")
    link_type: Literal["depends_on"] = Field(default="depends_on", alias="type")


class KanbanImportManifestV1(ContractModel):
    version: Literal["v1"] = "v1"
    tasks: list[KanbanTaskV1]
    links: list[KanbanLinkV1] = Field(default_factory=list)


def build_kanban_manifest(package: PromptPackageV1) -> KanbanImportManifestV1:
    validated = PromptPackageV1.model_validate(package.model_dump())
    if not validated.steps:
        raise ValueError("prompt package must contain at least one step")

    tasks: list[KanbanTaskV1] = []
    links: list[KanbanLinkV1] = []
    for step in validated.steps:
        if not step.prompt_markdown.strip():
            raise ValueError(f"step {step.step_index} missing prompt_markdown")
        tasks.append(
            KanbanTaskV1(
                external_task_key=step.external_task_key,
                title=step.title,
                prompt=step.prompt_markdown,
                base_ref=step.base_ref,
                agent_id=step.agent_id,
                start_in_plan_mode=step.start_in_plan_mode,
            )
        )
        for dependency_index in step.depends_on_step_indices:
            dependency = next((item for item in validated.steps if item.step_index == dependency_index), None)
            if dependency is None:
                continue
            links.append(
                KanbanLinkV1(
                    from_external_task_key=dependency.external_task_key,
                    to_external_task_key=step.external_task_key,
                )
            )

    return KanbanImportManifestV1(tasks=tasks, links=links)
