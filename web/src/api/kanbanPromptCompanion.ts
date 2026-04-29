import { fetchJson, postJson } from "@/api/client";
import type {
  AppSettingsSnapshot,
  DeliveryDetail,
  DeliveryListResponse,
  IntakeListResponse,
  KanbanPreviewResponse,
  ReviewListResponse,
  ReviewPackageDetail,
  WorkspaceListResponse,
} from "@/api/types";

function withQuery(path: string, query: Record<string, string | number | boolean | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined) {
      continue;
    }
    params.set(key, String(value));
  }
  const search = params.toString();
  return search ? `${path}?${search}` : path;
}

export function getIntakeNotes(status?: string, limit?: number) {
  return fetchJson<IntakeListResponse>(withQuery("/api/intake", { status, limit }));
}

export function getReviewQueue() {
  return fetchJson<ReviewListResponse>("/api/review");
}

export function getPackageDetail(packageId: string) {
  return fetchJson<ReviewPackageDetail>(`/api/packages/${packageId}`);
}

export function updatePackageWorkspace(packageId: string, workspaceId: string | null) {
  return fetchJson<{ package: ReviewPackageDetail }>(`/api/packages/${packageId}`, {
    method: "PATCH",
    body: JSON.stringify({ workspace_id: workspaceId }),
  });
}

export function patchPromptStep(
  stepId: string,
  payload: {
    title?: string;
    prompt_markdown?: string;
    base_ref?: string | null;
    agent_id?: string | null;
    start_in_plan_mode?: boolean;
  },
) {
  return fetchJson<{ step: Record<string, unknown> }>(`/api/steps/${stepId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function approvePackage(packageId: string, deliver = false) {
  return postJson<{ package: ReviewPackageDetail; delivery?: Record<string, unknown> }>(
    `/api/packages/${packageId}/approve`,
    { deliver },
  );
}

export function listKanbanWorkspaces() {
  return fetchJson<WorkspaceListResponse>("/api/kanban/workspaces");
}

export function previewKanbanPackage(packageId: string) {
  return postJson<KanbanPreviewResponse>(`/api/packages/${packageId}/kanban/preview`);
}

export function deliverKanbanPackage(packageId: string) {
  return postJson<{ delivery: DeliveryDetail["delivery"]; kanban_response?: unknown }>(
    `/api/packages/${packageId}/kanban/deliver`,
  );
}

export function listDeliveries() {
  return fetchJson<DeliveryListResponse>("/api/deliveries");
}

export function getDelivery(deliveryId: string) {
  return fetchJson<DeliveryDetail>(`/api/deliveries/${deliveryId}`);
}

export function retryDelivery(deliveryId: string) {
  return postJson<{ delivery: DeliveryDetail["delivery"]; kanban_response?: unknown }>(
    `/api/deliveries/${deliveryId}/retry`,
  );
}

export function loadLocalSettings(): AppSettingsSnapshot {
  return {
    kanbanBaseUrl: import.meta.env.VITE_KPC_KANBAN_BASE_URL ?? "http://127.0.0.1:3484",
    kanbanWorkspaceId: import.meta.env.VITE_KPC_KANBAN_WORKSPACE_ID ?? "",
    vaultPath: import.meta.env.VITE_KPC_VAULT_PATH ?? "Set in backend .env",
    watchFolder: import.meta.env.VITE_KPC_WATCH_FOLDER ?? "Inbox/Voice",
  };
}
