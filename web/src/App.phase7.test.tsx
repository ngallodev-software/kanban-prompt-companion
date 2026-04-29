import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "@/App";
import * as api from "@/api/kanbanPromptCompanion";

vi.mock("@/api/kanbanPromptCompanion", () => ({
  approvePackage: vi.fn(),
  deliverKanbanPackage: vi.fn(),
  getDelivery: vi.fn(),
  getIntakeNotes: vi.fn(),
  getPackageDetail: vi.fn(),
  getReviewQueue: vi.fn(),
  listDeliveries: vi.fn(),
  loadLocalSettings: vi.fn(),
  patchPromptStep: vi.fn(),
  previewKanbanPackage: vi.fn(),
  retryDelivery: vi.fn(),
}));

const mockedApi = vi.mocked(api);

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
}

function renderApp(pathname: string) {
  window.history.replaceState({}, "", pathname);
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  window.history.replaceState({}, "", "/intake");
});

describe("phase 7 review and delivery loop", () => {
  it("lets a user open review, edit, preview, and deliver a package", async () => {
    const user = userEvent.setup();
    mockedApi.getReviewQueue.mockResolvedValue({
      items: [
        {
          id: "pkg-1",
          note_id: "note-1",
          note_title: "Parser pipeline voice note",
          source_note_path: "/vault/Inbox/Voice/Parser pipeline voice note.md",
          source_note_title: "Parser pipeline voice note",
          status: "review_ready",
          requires_review: true,
          workspace_id: "kanban",
          created_at: "2026-04-28T09:10:00.000Z",
          updated_at: "2026-04-28T09:10:00.000Z",
          step_count: 1,
        },
      ],
    });
    mockedApi.getPackageDetail.mockResolvedValue({
      id: "pkg-1",
      note_id: "note-1",
      note_title: "Parser pipeline voice note",
      source_note_path: "/vault/Inbox/Voice/Parser pipeline voice note.md",
      source_note_title: "Parser pipeline voice note",
      status: "review_ready",
      requires_review: true,
      workspace_id: "kanban",
      cleaned_intent: "I need you to add a simple parser for the note intake flow.",
      project_key: "kanban",
      version: "v1",
      created_at: "2026-04-28T09:10:00.000Z",
      updated_at: "2026-04-28T09:10:00.000Z",
      error_message: null,
      steps: [
        {
          id: "step-1",
          package_id: "pkg-1",
          step_index: 1,
          external_task_key: "obsidian:inbox/voice/parser-pipeline-voice-note.md#step-1",
          title: "Parser cleanup",
          prompt_markdown: "Write the task cleanly.",
          base_ref: "main",
          agent_id: "codex",
          start_in_plan_mode: true,
          depends_on_step_indices: [],
          status: "draft",
          created_at: "2026-04-28T09:10:00.000Z",
          updated_at: "2026-04-28T09:10:00.000Z",
        },
      ],
    });
    mockedApi.patchPromptStep.mockResolvedValue({ step: {} });
    mockedApi.previewKanbanPackage.mockResolvedValue({
      package_id: "pkg-1",
      workspace_id: "kanban",
      procedure: "workspace.importTasks",
      payload: { tasks: [{ title: "Parser cleanup" }] },
      warnings: [],
    });
    mockedApi.deliverKanbanPackage.mockResolvedValue({
      delivery: {
        id: "del-1",
        package_id: "pkg-1",
        source_note_id: "note-1",
        source_note_title: "Parser pipeline voice note",
        source_note_path: "/vault/Inbox/Voice/Parser pipeline voice note.md",
        kanban_workspace_id: "kanban",
        request: { procedure: "workspace.importTasks" },
        response: { ok: true },
        status: "delivered",
        error_message: null,
        created_at: "2026-04-28T09:20:00.000Z",
        delivered_at: "2026-04-28T09:20:30.000Z",
      },
    });

    renderApp("/review?package=pkg-1");

    const prompt = await screen.findByLabelText("Prompt markdown");
    await user.clear(prompt);
    await user.type(prompt, "Rewrite the parser step with the updated constraint.");
    await user.click((await screen.findAllByRole("button", { name: "Save step" }))[0]!);
    await waitFor(() =>
      expect(mockedApi.patchPromptStep).toHaveBeenCalledWith("step-1", {
        title: "Parser cleanup",
        prompt_markdown: "Rewrite the parser step with the updated constraint.",
        base_ref: "main",
        agent_id: "codex",
        start_in_plan_mode: true,
      }),
    );

    await user.click((await screen.findAllByRole("button", { name: "Preview Kanban payload" }))[0]!);
    await waitFor(() => expect(mockedApi.previewKanbanPackage).toHaveBeenCalledWith("pkg-1"));
    expect(await screen.findByText(/workspace.importTasks/)).toBeInTheDocument();

    await user.click((await screen.findAllByRole("button", { name: "Deliver to Kanban" }))[0]!);
    await waitFor(() => expect(mockedApi.deliverKanbanPackage).toHaveBeenCalledWith("pkg-1"));
    expect(await screen.findByText("Delivered to Kanban.")).toBeInTheDocument();
  });

  it("shows failed deliveries and retry feedback", async () => {
    const user = userEvent.setup();
    mockedApi.listDeliveries.mockResolvedValue({
      items: [
        {
          id: "del-1",
          package_id: "pkg-1",
          source_note_id: "note-1",
          source_note_title: "Parser pipeline voice note",
          source_note_path: "/vault/Inbox/Voice/Parser pipeline voice note.md",
          kanban_workspace_id: "kanban",
          request: { procedure: "workspace.importTasks" },
          response: { ok: false },
          status: "failed",
          error_message: "workspace.importTasks failed: 500: BAD_REQUEST: missing workspace id",
          created_at: "2026-04-28T09:20:00.000Z",
          delivered_at: null,
        },
      ],
    });
    mockedApi.getDelivery.mockResolvedValue({
      delivery: {
        id: "del-1",
        package_id: "pkg-1",
        source_note_id: "note-1",
        source_note_title: "Parser pipeline voice note",
        source_note_path: "/vault/Inbox/Voice/Parser pipeline voice note.md",
        kanban_workspace_id: "kanban",
        request: { procedure: "workspace.importTasks" },
        response: { ok: false },
        status: "failed",
        error_message: "workspace.importTasks failed: 500: BAD_REQUEST: missing workspace id",
        created_at: "2026-04-28T09:20:00.000Z",
        delivered_at: null,
      },
    });
    mockedApi.retryDelivery.mockResolvedValue({
      delivery: {
        id: "del-1",
        package_id: "pkg-1",
        source_note_id: "note-1",
        source_note_title: "Parser pipeline voice note",
        source_note_path: "/vault/Inbox/Voice/Parser pipeline voice note.md",
        kanban_workspace_id: "kanban",
        request: { procedure: "workspace.importTasks" },
        response: { ok: true },
        status: "delivered",
        error_message: null,
        created_at: "2026-04-28T09:21:00.000Z",
        delivered_at: "2026-04-28T09:21:30.000Z",
      },
    });

    renderApp("/deliveries?delivery=del-1");

    expect(await screen.findByText("workspace.importTasks failed: 500: BAD_REQUEST: missing workspace id")).toBeInTheDocument();
    await user.click((await screen.findAllByRole("button", { name: "Retry failed delivery" }))[0]!);
    await waitFor(() => expect(mockedApi.retryDelivery).toHaveBeenCalledWith("del-1"));
  });
});
