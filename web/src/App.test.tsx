import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "@/App";
import { SafeMarkdownPreview } from "@/components/SafeMarkdownPreview";
import * as api from "@/api/kanbanPromptCompanion";

vi.mock("@/api/kanbanPromptCompanion", () => ({
  approvePackage: vi.fn(),
  deliverKanbanPackage: vi.fn(),
  getDelivery: vi.fn(),
  getIntakeNotes: vi.fn(),
  getPackageDetail: vi.fn(),
  getReviewQueue: vi.fn(),
  listDeliveries: vi.fn(),
  listKanbanWorkspaces: vi.fn(),
  loadLocalSettings: vi.fn(),
  patchPromptStep: vi.fn(),
  previewKanbanPackage: vi.fn(),
  retryDelivery: vi.fn(),
  updatePackageWorkspace: vi.fn(),
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
  mockedApi.listKanbanWorkspaces.mockResolvedValue({
    items: [
      { id: "kanban", name: "Kanban", path: "/vault/kanban" },
      { id: "product", name: "Product", path: "/vault/product" },
    ],
  });
  window.history.replaceState({}, "", "/intake");
});

afterEach(() => {
  cleanup();
});

describe("Kanban Prompt Companion UI", () => {
  it("renders intake notes", async () => {
    mockedApi.getIntakeNotes.mockResolvedValue({
      items: [
        {
          id: "note-1",
          status: "parsed",
          title: "Weekly planning voice note",
          relative_path: "inbox/weekly.md",
          discovered_at: "2026-04-28T09:00:00.000Z",
          last_seen_at: "2026-04-28T09:03:00.000Z",
          error_message: null,
          package: {
            id: "pkg-1",
            status: "review_ready",
            requires_review: true,
            workspace_id: "kanban",
            step_count: 1,
          },
        },
        {
          id: "note-2",
          status: "failed",
          title: "Sprint review follow-up",
          relative_path: "inbox/sprint.md",
          discovered_at: "2026-04-28T10:00:00.000Z",
          last_seen_at: "2026-04-28T10:05:00.000Z",
          error_message: "Transcript parse failed.",
          package: null,
        },
      ],
    });

    renderApp("/intake");

    expect(await screen.findAllByText("Weekly planning voice note")).not.toHaveLength(0);
    expect(screen.getAllByText("inbox/weekly.md")).not.toHaveLength(0);
    expect(screen.getByText("Transcript parse failed.")).toBeInTheDocument();
  });

  it("renders package detail and step editor", async () => {
    mockedApi.getReviewQueue.mockResolvedValue({
      items: [
        {
          id: "pkg-1",
          note_id: "note-1",
          note_title: "Weekly planning voice note",
          source_note_path: "/vault/inbox/weekly.md",
          source_note_title: "Weekly planning voice note",
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
      note_title: "Weekly planning voice note",
      source_note_path: "/vault/inbox/weekly.md",
      source_note_title: "Weekly planning voice note",
      status: "review_ready",
      requires_review: true,
      workspace_id: "kanban",
      cleaned_intent: "Turn the note into a concise task package.",
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
          external_task_key: "pkg-1-step-1",
          title: "Draft task",
          prompt_markdown: "Write the task cleanly.",
          base_ref: "main",
          agent_id: "agent-a",
          start_in_plan_mode: true,
          depends_on_step_indices: [],
          status: "draft",
          created_at: "2026-04-28T09:10:00.000Z",
          updated_at: "2026-04-28T09:10:00.000Z",
        },
      ],
    });

    renderApp("/review?package=pkg-1");

    expect(await screen.findAllByText("Weekly planning voice note")).not.toHaveLength(0);
    expect(await screen.findByLabelText("Step title")).toHaveValue("Draft task");
  });

  it("selects a kanban workspace for the review package", async () => {
    const user = userEvent.setup();
    mockedApi.getReviewQueue.mockResolvedValue({
      items: [
        {
          id: "pkg-1",
          note_id: "note-1",
          note_title: "Weekly planning voice note",
          source_note_path: "/vault/inbox/weekly.md",
          source_note_title: "Weekly planning voice note",
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
      note_title: "Weekly planning voice note",
      source_note_path: "/vault/inbox/weekly.md",
      source_note_title: "Weekly planning voice note",
      status: "review_ready",
      requires_review: true,
      workspace_id: "kanban",
      cleaned_intent: "Turn the note into a concise task package.",
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
          external_task_key: "pkg-1-step-1",
          title: "Draft task",
          prompt_markdown: "Write the task cleanly.",
          base_ref: "main",
          agent_id: "agent-a",
          start_in_plan_mode: true,
          depends_on_step_indices: [],
          status: "draft",
          created_at: "2026-04-28T09:10:00.000Z",
          updated_at: "2026-04-28T09:10:00.000Z",
        },
      ],
    });
    mockedApi.updatePackageWorkspace.mockResolvedValue({
      package: {
        id: "pkg-1",
        note_id: "note-1",
        note_title: "Weekly planning voice note",
        source_note_path: "/vault/inbox/weekly.md",
        source_note_title: "Weekly planning voice note",
        status: "review_ready",
        requires_review: true,
        workspace_id: "product",
        cleaned_intent: "Turn the note into a concise task package.",
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
            external_task_key: "pkg-1-step-1",
            title: "Draft task",
            prompt_markdown: "Write the task cleanly.",
            base_ref: "main",
            agent_id: "agent-a",
            start_in_plan_mode: true,
            depends_on_step_indices: [],
            status: "draft",
            created_at: "2026-04-28T09:10:00.000Z",
            updated_at: "2026-04-28T09:10:00.000Z",
          },
        ],
      },
    });

    renderApp("/review?package=pkg-1");

    const workspaceSelect = await screen.findByLabelText("Kanban workspace");
    expect(workspaceSelect).toHaveValue("kanban");
    await user.selectOptions(workspaceSelect, "product");

    await waitFor(() =>
      expect(mockedApi.updatePackageWorkspace).toHaveBeenCalledWith("pkg-1", "product"),
    );
  });

  it("shows kanban offline state when workspace discovery fails", async () => {
    mockedApi.listKanbanWorkspaces.mockRejectedValueOnce(new Error("kanban connection error: connect ECONNREFUSED"));
    mockedApi.getReviewQueue.mockResolvedValue({
      items: [
        {
          id: "pkg-1",
          note_id: "note-1",
          note_title: "Weekly planning voice note",
          source_note_path: "/vault/inbox/weekly.md",
          source_note_title: "Weekly planning voice note",
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
      note_title: "Weekly planning voice note",
      source_note_path: "/vault/inbox/weekly.md",
      source_note_title: "Weekly planning voice note",
      status: "review_ready",
      requires_review: true,
      workspace_id: "kanban",
      cleaned_intent: "Turn the note into a concise task package.",
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
          external_task_key: "pkg-1-step-1",
          title: "Draft task",
          prompt_markdown: "Write the task cleanly.",
          base_ref: "main",
          agent_id: "agent-a",
          start_in_plan_mode: true,
          depends_on_step_indices: [],
          status: "draft",
          created_at: "2026-04-28T09:10:00.000Z",
          updated_at: "2026-04-28T09:10:00.000Z",
        },
      ],
    });

    renderApp("/review?package=pkg-1");

    expect(await screen.findByText(/Kanban instance unavailable/i)).toBeInTheDocument();
  });

  it("saves step edits through PATCH", async () => {
    const user = userEvent.setup();
    mockedApi.getReviewQueue.mockResolvedValue({
      items: [
        {
          id: "pkg-1",
          note_id: "note-1",
          note_title: "Weekly planning voice note",
          source_note_path: "/vault/inbox/weekly.md",
          source_note_title: "Weekly planning voice note",
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
      note_title: "Weekly planning voice note",
      source_note_path: "/vault/inbox/weekly.md",
      source_note_title: "Weekly planning voice note",
      status: "review_ready",
      requires_review: true,
      workspace_id: "kanban",
      cleaned_intent: "Turn the note into a concise task package.",
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
          external_task_key: "pkg-1-step-1",
          title: "Draft task",
          prompt_markdown: "Write the task cleanly.",
          base_ref: "main",
          agent_id: "agent-a",
          start_in_plan_mode: true,
          depends_on_step_indices: [],
          status: "draft",
          created_at: "2026-04-28T09:10:00.000Z",
          updated_at: "2026-04-28T09:10:00.000Z",
        },
      ],
    });
    mockedApi.patchPromptStep.mockResolvedValue({ step: {} });

    renderApp("/review?package=pkg-1");

    const prompt = await screen.findByLabelText("Prompt markdown");
    await user.clear(prompt);
    await user.type(prompt, "Rewrite the task with tighter language.");
    await user.click((await screen.findAllByRole("button", { name: "Save step" }))[0]!);

    await waitFor(() =>
      expect(mockedApi.patchPromptStep).toHaveBeenCalledWith("step-1", {
        title: "Draft task",
        prompt_markdown: "Rewrite the task with tighter language.",
        base_ref: "main",
        agent_id: "agent-a",
        start_in_plan_mode: true,
      }),
    );
  });

  it("previews the Kanban payload", async () => {
    const user = userEvent.setup();
    mockedApi.getReviewQueue.mockResolvedValue({
      items: [
        {
          id: "pkg-1",
          note_id: "note-1",
          note_title: "Weekly planning voice note",
          source_note_path: "/vault/inbox/weekly.md",
          source_note_title: "Weekly planning voice note",
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
      note_title: "Weekly planning voice note",
      source_note_path: "/vault/inbox/weekly.md",
      source_note_title: "Weekly planning voice note",
      status: "review_ready",
      requires_review: true,
      workspace_id: "kanban",
      cleaned_intent: "Turn the note into a concise task package.",
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
          external_task_key: "pkg-1-step-1",
          title: "Draft task",
          prompt_markdown: "Write the task cleanly.",
          base_ref: "main",
          agent_id: "agent-a",
          start_in_plan_mode: true,
          depends_on_step_indices: [],
          status: "draft",
          created_at: "2026-04-28T09:10:00.000Z",
          updated_at: "2026-04-28T09:10:00.000Z",
        },
      ],
    });
    mockedApi.previewKanbanPackage.mockResolvedValue({
      package_id: "pkg-1",
      workspace_id: "kanban",
      procedure: "workspace.importTasks",
      payload: { tasks: [{ title: "Draft task" }] },
      warnings: [],
    });

    renderApp("/review?package=pkg-1");
    await user.click((await screen.findAllByRole("button", { name: "Preview Kanban payload" }))[0]!);

    await waitFor(() => expect(mockedApi.previewKanbanPackage).toHaveBeenCalledWith("pkg-1"));
    expect(screen.getByText(/workspace.importTasks/)).toBeInTheDocument();
  });

  it("delivers to Kanban and shows the result", async () => {
    const user = userEvent.setup();
    mockedApi.getReviewQueue.mockResolvedValue({
      items: [
        {
          id: "pkg-1",
          note_id: "note-1",
          note_title: "Weekly planning voice note",
          source_note_path: "/vault/inbox/weekly.md",
          source_note_title: "Weekly planning voice note",
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
      note_title: "Weekly planning voice note",
      source_note_path: "/vault/inbox/weekly.md",
      source_note_title: "Weekly planning voice note",
      status: "review_ready",
      requires_review: true,
      workspace_id: "kanban",
      cleaned_intent: "Turn the note into a concise task package.",
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
          external_task_key: "pkg-1-step-1",
          title: "Draft task",
          prompt_markdown: "Write the task cleanly.",
          base_ref: "main",
          agent_id: "agent-a",
          start_in_plan_mode: true,
          depends_on_step_indices: [],
          status: "draft",
          created_at: "2026-04-28T09:10:00.000Z",
          updated_at: "2026-04-28T09:10:00.000Z",
        },
      ],
    });
    mockedApi.deliverKanbanPackage.mockResolvedValue({
      delivery: {
        id: "del-1",
        package_id: "pkg-1",
        source_note_id: "note-1",
        source_note_title: "Weekly planning voice note",
        source_note_path: "/vault/inbox/weekly.md",
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
    await user.click((await screen.findAllByRole("button", { name: "Deliver to Kanban" }))[0]!);

    await waitFor(() => expect(mockedApi.deliverKanbanPackage).toHaveBeenCalledWith("pkg-1"));
    expect(await screen.findByText("Delivered to Kanban.")).toBeInTheDocument();
  });

  it("shows retry for failed deliveries", async () => {
    const user = userEvent.setup();
    mockedApi.listDeliveries.mockResolvedValue({
      items: [
        {
          id: "del-1",
          package_id: "pkg-1",
          source_note_id: "note-1",
          source_note_title: "Weekly planning voice note",
          source_note_path: "/vault/inbox/weekly.md",
          kanban_workspace_id: "kanban",
          request: { procedure: "workspace.importTasks" },
          response: { ok: false },
          status: "failed",
          error_message: "Kanban connection error.",
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
        source_note_title: "Weekly planning voice note",
        source_note_path: "/vault/inbox/weekly.md",
        kanban_workspace_id: "kanban",
        request: { procedure: "workspace.importTasks" },
        response: { ok: false },
        status: "failed",
        error_message: "Kanban connection error.",
        created_at: "2026-04-28T09:20:00.000Z",
        delivered_at: null,
      },
    });
    mockedApi.retryDelivery.mockResolvedValue({
      delivery: {
        id: "del-1",
        package_id: "pkg-1",
        source_note_id: "note-1",
        source_note_title: "Weekly planning voice note",
        source_note_path: "/vault/inbox/weekly.md",
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

    expect(await screen.findByText("Kanban connection error.")).toBeInTheDocument();
    const retryButtons = await screen.findAllByRole("button", { name: "Retry failed delivery" });
    expect(retryButtons[0]).toBeInTheDocument();
    await user.click(retryButtons[0]!);

    await waitFor(() => expect(mockedApi.retryDelivery).toHaveBeenCalledWith("del-1"));
  });

  it("keeps markdown preview free of raw HTML execution", () => {
    const { container } = render(<SafeMarkdownPreview markdown={"# Heading\n<script>alert(1)</script>"} />);

    expect(container.querySelector("script")).toBeNull();
    expect(screen.getByText("<script>alert(1)</script>")).toBeInTheDocument();
  });
});
