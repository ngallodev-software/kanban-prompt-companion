export type ScreenPath = "/intake" | "/review" | "/deliveries" | "/settings";

export interface IntakePackageLink {
  id: string;
  status: string;
  requires_review: boolean;
  workspace_id: string | null;
  step_count: number;
}

export interface IntakeNoteSummary {
  id: string;
  status: string;
  title: string;
  relative_path: string;
  discovered_at: string;
  last_seen_at: string;
  error_message: string | null;
  package: IntakePackageLink | null;
}

export interface IntakeNoteDetail extends IntakeNoteSummary {
  absolute_path: string;
  transcript: string;
  raw_body: string;
  frontmatter: Record<string, unknown>;
  cleaned_intent?: string;
}

export interface PromptStep {
  id: string;
  package_id: string;
  step_index: number;
  external_task_key: string;
  title: string;
  prompt_markdown: string;
  base_ref: string | null;
  agent_id: string | null;
  start_in_plan_mode: boolean;
  depends_on_step_indices: number[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ReviewPackageSummary {
  id: string;
  note_id: string;
  note_title: string;
  source_note_path: string;
  source_note_title: string;
  status: string;
  requires_review: boolean;
  workspace_id: string | null;
  created_at: string;
  updated_at: string;
  step_count: number;
}

export interface ReviewPackageDetail extends Omit<ReviewPackageSummary, "step_count"> {
  cleaned_intent: string;
  project_key: string | null;
  version: string;
  error_message: string | null;
  steps: PromptStep[];
}

export interface KanbanPreviewResponse {
  package_id: string;
  workspace_id: string | null;
  procedure: string;
  payload: unknown;
  warnings: string[];
}

export interface DeliverySummary {
  id: string;
  package_id: string;
  source_note_id: string;
  source_note_title: string;
  source_note_path: string;
  kanban_workspace_id: string;
  request: unknown;
  response: unknown;
  status: string;
  error_message: string | null;
  created_at: string;
  delivered_at: string | null;
}

export interface DeliveryDetail {
  delivery: DeliverySummary;
}

export interface WorkspaceSummary {
  id: string | null;
  name: string;
  path: string | null;
}

export interface IntakeListResponse {
  items: IntakeNoteSummary[];
}

export interface ReviewListResponse {
  items: ReviewPackageSummary[];
}

export interface DeliveryListResponse {
  items: DeliverySummary[];
}

export interface WorkspaceListResponse {
  items: WorkspaceSummary[];
}

export interface AppSettingsSnapshot {
  kanbanBaseUrl: string;
  kanbanWorkspaceId: string;
  vaultPath: string;
  watchFolder: string;
}
