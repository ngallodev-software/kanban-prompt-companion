import {
  ArrowRight,
  ClipboardList,
  Copy,
  Eye,
  FileText,
  Package,
  RefreshCw,
  RotateCcw,
  Send,
  Settings2,
  SquarePen,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  approvePackage,
  deliverKanbanPackage,
  getDelivery,
  getIntakeNotes,
  getPackageDetail,
  getReviewQueue,
  listDeliveries,
  listKanbanWorkspaces,
  loadLocalSettings,
  patchPromptStep,
  previewKanbanPackage,
  retryDelivery,
  updatePackageWorkspace,
} from "@/api/kanbanPromptCompanion";
import type { ScreenPath } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { StatusBadge, type StatusTone } from "@/components/ui/StatusBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/Table";
import { Textarea } from "@/components/ui/Textarea";
import { SafeMarkdownPreview } from "@/components/SafeMarkdownPreview";
import { cn } from "@/lib/cn";

type LocationState = { pathname: ScreenPath; search: string };
type RouteSelection = { packageId: string | null; deliveryId: string | null };
type WorkspaceOption = { id: string | null; name: string; path: string | null };
type ReviewDraft = {
  title: string;
  prompt_markdown: string;
  base_ref: string;
  agent_id: string;
  start_in_plan_mode: boolean;
};

const routes: Array<{ path: ScreenPath; label: string; icon: typeof ClipboardList; description: string }> = [
  { path: "/intake", label: "Intake", icon: ClipboardList, description: "See notes as they land." },
  { path: "/review", label: "Review", icon: SquarePen, description: "Edit prompt packages." },
  { path: "/deliveries", label: "Deliveries", icon: ArrowRight, description: "Track Kanban pushes." },
  { path: "/settings", label: "Settings", icon: Settings2, description: "Read local config only." },
];

const statusToneMap: Record<string, StatusTone> = {
  queued: "blue",
  parsed: "blue",
  cleaning: "cyan",
  review: "purple",
  review_ready: "purple",
  ready: "green",
  approved: "green",
  delivered: "green",
  sent: "green",
  delivering: "orange",
  pending: "orange",
  failed: "red",
  error: "red",
};

function normalizePathname(pathname: string): ScreenPath {
  if (pathname === "/review" || pathname.startsWith("/review/")) {
    return "/review";
  }
  if (pathname === "/deliveries" || pathname.startsWith("/deliveries/")) {
    return "/deliveries";
  }
  if (pathname === "/settings") {
    return "/settings";
  }
  return "/intake";
}

function parseLocation(): LocationState {
  return { pathname: normalizePathname(window.location.pathname), search: window.location.search };
}

function buildPath(pathname: ScreenPath, search: Record<string, string | null | undefined> = {}): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(search)) {
    if (value) {
      params.set(key, value);
    }
  }
  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

function parseSelection(search: string): RouteSelection {
  const params = new URLSearchParams(search);
  return {
    packageId: params.get("package"),
    deliveryId: params.get("delivery"),
  };
}

function formatRelativeTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  const diff = Date.now() - date.getTime();
  const minute = 60_000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) return "just now";
  if (diff < hour) return `${Math.max(1, Math.round(diff / minute))}m ago`;
  if (diff < day) return `${Math.max(1, Math.round(diff / hour))}h ago`;
  return `${Math.max(1, Math.round(diff / day))}d ago`;
}

function formatTimestamp(timestamp: string | null | undefined): string {
  if (!timestamp) {
    return "—";
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function jsonStringify(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function workspaceLabel(workspace: WorkspaceOption | undefined): string {
  if (!workspace) {
    return "Configured workspace";
  }
  return workspace.path ? `${workspace.name} · ${workspace.path}` : workspace.name;
}

function screenTitle(pathname: ScreenPath): string {
  return routes.find((route) => route.path === pathname)?.label ?? "Intake";
}

function screenDescription(pathname: ScreenPath): string {
  switch (pathname) {
    case "/intake":
      return "See new notes, their latest package state, and any failure text.";
    case "/review":
      return "Inspect package steps, edit the prompt, preview the Kanban payload, and deliver it.";
    case "/deliveries":
      return "Track delivery status, inspect request and response JSON, and retry failures.";
    case "/settings":
      return "Read the local Kanban and vault settings that are configured outside the app.";
  }
}

function useBrowserLocation() {
  const [location, setLocation] = useState<LocationState>(() => parseLocation());

  useEffect(() => {
    const sync = () => setLocation(parseLocation());
    window.addEventListener("popstate", sync);
    if (!["/intake", "/review", "/deliveries", "/settings"].includes(window.location.pathname)) {
      window.history.replaceState({}, "", "/intake");
      sync();
    }
    return () => window.removeEventListener("popstate", sync);
  }, []);

  const navigate = useCallback((pathname: ScreenPath, search: Record<string, string | null | undefined> = {}) => {
    const nextPath = buildPath(pathname, search);
    window.history.pushState({}, "", nextPath);
    setLocation({ pathname, search: new URL(nextPath, window.location.origin).search });
  }, []);

  return { location, navigate };
}

export default function App() {
  const queryClient = useQueryClient();
  const { location, navigate } = useBrowserLocation();
  const pathname = location.pathname;
  const selection = useMemo(() => parseSelection(location.search), [location.search]);
  const routeLabel = screenTitle(pathname);
  const routeDescription = screenDescription(pathname);

  return (
    <main className="min-h-screen bg-surface-0 text-text-primary">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-4 px-4 py-4 lg:px-6">
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-divider pb-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-lg font-semibold tracking-tight sm:text-xl">Kanban Prompt Companion</h1>
              <Badge variant="secondary">Minimal review UI</Badge>
            </div>
            <p className="max-w-2xl text-sm text-text-secondary">
              Obsidian note intake, prompt package review, Kanban payload preview, delivery status, and retry only.
            </p>
          </div>

          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-text-tertiary">Screen</p>
            <p className="text-sm font-medium text-text-primary">{routeLabel}</p>
          </div>
        </header>

        <nav aria-label="Primary" className="flex flex-wrap gap-2 border-b border-divider pb-4" role="tablist">
          {routes.map((route) => {
            const active = route.path === pathname;
            const Icon = route.icon;
            return (
              <Button
                key={route.path}
                aria-selected={active}
                className={cn(
                  "justify-start",
                  active ? "bg-surface-2 text-text-primary" : "text-text-secondary",
                )}
                onClick={() => navigate(route.path)}
                role="tab"
                size="sm"
                variant={active ? "outline" : "ghost"}
              >
                <Icon size={14} />
                {route.label}
              </Button>
            );
          })}
        </nav>

        <section className="grid gap-4 xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.95fr)]">
          <Card className="min-w-0">
            <CardHeader>
              <CardTitle>{routeLabel}</CardTitle>
              <CardDescription>{routeDescription}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {pathname === "/intake" && (
                <IntakeScreen navigate={navigate} selection={selection} queryClient={queryClient} />
              )}
              {pathname === "/review" && (
                <ReviewScreen
                  navigate={navigate}
                  packageSelection={selection.packageId}
                  queryClient={queryClient}
                />
              )}
              {pathname === "/deliveries" && (
                <DeliveriesScreen
                  deliverySelection={selection.deliveryId}
                  navigate={navigate}
                  queryClient={queryClient}
                />
              )}
              {pathname === "/settings" && <SettingsScreen />}
            </CardContent>
          </Card>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Loop</CardTitle>
                <CardDescription>The minimum path from note to Kanban task package.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-text-secondary">
                <div className="grid gap-2">
                  <div className="flex items-center gap-2">
                    <StatusBadge label="Intake" tone="blue" />
                    <span>See note state and open review.</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge label="Review" tone="purple" />
                    <span>Edit step markdown and preview payloads.</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge label="Delivery" tone="green" />
                    <span>Deliver to Kanban and retry failures.</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* <Card>
              <CardHeader>
                <CardTitle>Scope</CardTitle>
                <CardDescription>Nothing beyond the requested screens and API surface.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-text-secondary">
                <p>No admin shell.</p>
                <p>No dashboards, charts, routing registry, or role controls.</p>
                <p>No direct Kanban state writes.</p>
              </CardContent>
            </Card> */}
          </div>
        </section>
      </div>
    </main>
  );
}

function IntakeScreen({
  navigate,
  selection,
  queryClient,
}: {
  navigate: (pathname: ScreenPath, search?: Record<string, string | null | undefined>) => void;
  selection: RouteSelection;
  queryClient: ReturnType<typeof useQueryClient>;
}) {
  const intakeQuery = useQuery({ queryKey: ["intake"], queryFn: () => getIntakeNotes(), staleTime: 5_000 });
  const [statusFilter, setStatusFilter] = useState("all");
  const refreshIntake = async () => {
    await queryClient.invalidateQueries({ queryKey: ["intake"] });
  };

  const notes = intakeQuery.data?.items ?? [];
  const statuses = useMemo(() => ["all", ...new Set(notes.map((note) => note.status))], [notes]);
  const filteredNotes =
    statusFilter === "all" ? notes : notes.filter((note) => note.status === statusFilter);
  const selectedNote =
    filteredNotes.find((note) => note.package?.id === selection.packageId || note.id === selection.packageId) ??
    filteredNotes[0] ??
    null;

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(280px,0.7fr)]">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs uppercase tracking-wide text-text-tertiary" htmlFor="intake-status-filter">
            Status
          </label>
          <select
            id="intake-status-filter"
            className="h-9 rounded-md border border-border bg-surface-1 px-3 text-sm text-text-primary"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            {statuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
          <Button variant="secondary" size="sm" onClick={refreshIntake} disabled={intakeQuery.isFetching}>
            <RefreshCw size={14} />
            Refresh
          </Button>
        </div>

        {intakeQuery.isLoading ? (
          <p className="text-sm text-text-secondary">Loading intake notes.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Note</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Seen</TableHead>
                <TableHead>Package</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredNotes.map((note) => (
                <TableRow
                  key={note.id}
                  className={cn(note.id === selectedNote?.id ? "bg-surface-2" : "")}
                  onClick={() => navigate("/intake", { package: note.package?.id ?? note.id })}
                >
                  <TableCell className="space-y-1">
                    <p className="font-medium text-text-primary">{note.title}</p>
                    <p className="text-xs text-text-tertiary">{note.relative_path}</p>
                    {note.error_message ? <p className="text-xs text-status-red">{note.error_message}</p> : null}
                  </TableCell>
                  <TableCell>
                    <StatusBadge label={note.status} tone={statusToneMap[note.status] ?? "blue"} />
                  </TableCell>
                  <TableCell className="text-xs text-text-secondary">
                    <div>{formatRelativeTimestamp(note.last_seen_at)}</div>
                    <div>{formatTimestamp(note.discovered_at)}</div>
                  </TableCell>
                  <TableCell className="text-xs text-text-secondary">
                    {note.package ? (
                      <div className="space-y-1">
                        <StatusBadge label={note.package.status} tone={statusToneMap[note.package.status] ?? "blue"} />
                        <p>{note.package.step_count} steps</p>
                      </div>
                    ) : (
                      "No package yet"
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <Card className="h-fit">
        <CardHeader>
          <CardTitle>{selectedNote ? selectedNote.title : "Select a note"}</CardTitle>
          <CardDescription>{selectedNote?.relative_path ?? "No note selected yet."}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {selectedNote ? (
            <>
              <div className="grid gap-2 text-text-secondary">
                <div className="flex justify-between gap-4">
                  <span>Status</span>
                  <StatusBadge label={selectedNote.status} tone={statusToneMap[selectedNote.status] ?? "blue"} />
                </div>
                <div className="flex justify-between gap-4">
                  <span>Last seen</span>
                  <span className="text-text-primary">{formatTimestamp(selectedNote.last_seen_at)}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span>Discovered</span>
                  <span className="text-text-primary">{formatTimestamp(selectedNote.discovered_at)}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span>Package</span>
                  <span className="text-text-primary">{selectedNote.package?.status ?? "none"}</span>
                </div>
              </div>

              {selectedNote.error_message ? (
                <div className="rounded-md border border-status-red/40 bg-status-red/10 px-3 py-2 text-xs text-status-red">
                  {selectedNote.error_message}
                </div>
              ) : null}

              {selectedNote.package?.id ? (
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" onClick={() => navigate("/review", { package: selectedNote.package?.id })}>
                    <FileText size={14} />
                    Open review package
                  </Button>
                </div>
              ) : null}
            </>
          ) : (
            <p className="text-text-tertiary">Pick a note row to see the compact intake summary.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ReviewScreen({
  navigate,
  packageSelection,
  queryClient,
}: {
  navigate: (pathname: ScreenPath, search?: Record<string, string | null | undefined>) => void;
  packageSelection: string | null;
  queryClient: ReturnType<typeof useQueryClient>;
}) {
  const reviewQuery = useQuery({ queryKey: ["review"], queryFn: getReviewQueue, staleTime: 5_000 });
  const workspacesQuery = useQuery({ queryKey: ["kanban-workspaces"], queryFn: listKanbanWorkspaces, staleTime: 30_000 });
  const reviewPackages = reviewQuery.data?.items ?? [];
  const selectedPackageId = packageSelection ?? reviewPackages[0]?.id ?? null;
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const packageQuery = useQuery({
    queryKey: ["package", selectedPackageId],
    queryFn: () => getPackageDetail(selectedPackageId ?? ""),
    enabled: Boolean(selectedPackageId),
    staleTime: 5_000,
  });

  const packageDetail = packageQuery.data ?? null;
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [draft, setDraft] = useState<ReviewDraft | null>(null);
  const [previewResult, setPreviewResult] = useState<unknown>(null);
  const [deliveryResult, setDeliveryResult] = useState<unknown>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    setSelectedWorkspaceId(packageDetail?.workspace_id ?? null);
  }, [packageDetail?.id, packageDetail?.workspace_id]);

  useEffect(() => {
    const firstStep = packageDetail?.steps[0] ?? null;
    setSelectedStepId(firstStep?.id ?? null);
    setDraft(
      firstStep
        ? {
            title: firstStep.title,
            prompt_markdown: firstStep.prompt_markdown,
            base_ref: firstStep.base_ref ?? "",
            agent_id: firstStep.agent_id ?? "",
            start_in_plan_mode: firstStep.start_in_plan_mode,
          }
        : null,
    );
    setPreviewResult(null);
    setDeliveryResult(null);
    setActionMessage(null);
  }, [packageDetail?.id]);

  const selectedStep = packageDetail?.steps.find((step) => step.id === selectedStepId) ?? packageDetail?.steps[0] ?? null;

  useEffect(() => {
    if (!selectedStep) {
      return;
    }
    setDraft({
      title: selectedStep.title,
      prompt_markdown: selectedStep.prompt_markdown,
      base_ref: selectedStep.base_ref ?? "",
      agent_id: selectedStep.agent_id ?? "",
      start_in_plan_mode: selectedStep.start_in_plan_mode,
    });
  }, [selectedStep?.id]);

  const saveStep = useMutation({
    mutationFn: ({ stepId, payload }: { stepId: string; payload: ReviewDraft }) =>
      patchPromptStep(stepId, {
        title: payload.title,
        prompt_markdown: payload.prompt_markdown,
        base_ref: payload.base_ref || null,
        agent_id: payload.agent_id || null,
        start_in_plan_mode: payload.start_in_plan_mode,
      }),
    onSuccess: async () => {
      setActionMessage("Step saved.");
      await queryClient.invalidateQueries({ queryKey: ["package", selectedPackageId] });
    },
  });

  const approve = useMutation({
    mutationFn: () => approvePackage(selectedPackageId ?? "", false),
    onSuccess: async (response) => {
      setActionMessage("Package approved.");
      setDeliveryResult(response.delivery ?? null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["review"] }),
        queryClient.invalidateQueries({ queryKey: ["package", selectedPackageId] }),
        queryClient.invalidateQueries({ queryKey: ["intake"] }),
      ]);
    },
  });

  const preview = useMutation({
    mutationFn: () => previewKanbanPackage(selectedPackageId ?? ""),
    onSuccess: (response) => {
      setPreviewResult(response);
      setActionMessage("Kanban payload preview refreshed.");
    },
  });

  const updateWorkspace = useMutation({
    mutationFn: ({ packageId, workspaceId }: { packageId: string; workspaceId: string | null }) =>
      updatePackageWorkspace(packageId, workspaceId),
    onSuccess: async (response) => {
      const nextWorkspaceId = response.package.workspace_id ?? null;
      setSelectedWorkspaceId(nextWorkspaceId);
      setActionMessage(nextWorkspaceId ? "Workspace updated." : "Workspace cleared.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["review"] }),
        queryClient.invalidateQueries({ queryKey: ["package", selectedPackageId] }),
        queryClient.invalidateQueries({ queryKey: ["intake"] }),
      ]);
    },
    onError: () => {
      setSelectedWorkspaceId(packageDetail?.workspace_id ?? null);
      setActionMessage("Unable to update workspace.");
    },
  });

  const refreshReview = async () => {
    await Promise.all([reviewQuery.refetch(), packageQuery.refetch()]);
    setActionMessage("Review queue refreshed.");
  };

  const workspaceOptions = [
    ...(workspacesQuery.data?.items ?? []).map((workspace) => ({
      id: workspace.id,
      name: workspace.name,
      path: workspace.path,
    })),
    ...(selectedWorkspaceId &&
    !(workspacesQuery.data?.items ?? []).some((workspace) => workspace.id === selectedWorkspaceId)
      ? [{ id: selectedWorkspaceId, name: selectedWorkspaceId, path: null }]
      : []),
  ];

  const deliver = useMutation({
    mutationFn: () => deliverKanbanPackage(selectedPackageId ?? ""),
    onSuccess: async (response) => {
      setDeliveryResult(response);
      setActionMessage(response.delivery?.status === "delivered" ? "Delivered to Kanban." : "Delivery failed.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["review"] }),
        queryClient.invalidateQueries({ queryKey: ["package", selectedPackageId] }),
        queryClient.invalidateQueries({ queryKey: ["deliveries"] }),
        queryClient.invalidateQueries({ queryKey: ["intake"] }),
      ]);
    },
  });

  const isDirty =
    Boolean(
      selectedStep &&
        draft &&
        (selectedStep.title !== draft.title ||
          selectedStep.prompt_markdown !== draft.prompt_markdown ||
          (selectedStep.base_ref ?? "") !== draft.base_ref ||
          (selectedStep.agent_id ?? "") !== draft.agent_id ||
          selectedStep.start_in_plan_mode !== draft.start_in_plan_mode),
    );

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-2">
          <div className="text-xs uppercase tracking-wide text-text-tertiary">Review queue</div>
          <Button variant="secondary" size="sm" onClick={refreshReview} disabled={reviewQuery.isFetching}>
            <RefreshCw size={14} />
            Refresh
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Package</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Steps</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reviewPackages.map((item) => (
              <TableRow
                key={item.id}
                className={cn(item.id === selectedPackageId ? "bg-surface-2" : "")}
                onClick={() => navigate("/review", { package: item.id })}
              >
                <TableCell className="space-y-1">
                  <p className="font-medium text-text-primary">{item.note_title}</p>
                  <p className="text-xs text-text-tertiary">{item.source_note_path}</p>
                </TableCell>
                <TableCell>
                  <StatusBadge label={item.status} tone={statusToneMap[item.status] ?? "blue"} />
                </TableCell>
                <TableCell className="text-xs text-text-secondary">{item.step_count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {packageDetail ? (
          <Card>
            <CardHeader>
              <CardTitle>Package detail</CardTitle>
              <CardDescription>{packageDetail.source_note_path}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {workspacesQuery.isError ? (
                <div className="rounded-md border border-status-red/40 bg-status-red/10 px-3 py-2 text-xs text-status-red">
                  Kanban instance unavailable:{" "}
                  {workspacesQuery.error instanceof Error ? workspacesQuery.error.message : "Unable to load workspaces."}
                </div>
              ) : null}

                <div className="grid gap-2 text-sm text-text-secondary sm:grid-cols-2">
                  <div className="flex justify-between gap-4">
                    <span>Status</span>
                    <StatusBadge label={packageDetail.status} tone={statusToneMap[packageDetail.status] ?? "blue"} />
                  </div>
                  <div className="flex justify-between gap-4">
                    <span>Project</span>
                    <span className="text-text-primary">{packageDetail.project_key ?? "kanban"}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span>Version</span>
                    <span className="text-text-primary">{packageDetail.version}</span>
                  </div>
                  <div className="space-y-2 sm:col-span-2">
                    <div className="flex items-center justify-between gap-4">
                      <span>Kanban workspace</span>
                      <StatusBadge
                        label={workspacesQuery.isError ? "offline" : workspacesQuery.isLoading ? "loading" : "ready"}
                        tone={workspacesQuery.isError ? "red" : workspacesQuery.isLoading ? "orange" : "green"}
                      />
                    </div>
                    {workspacesQuery.isLoading ? (
                      <p className="text-xs text-text-tertiary">Discovering workspaces from the running Kanban instance.</p>
                    ) : (
                      <select
                        aria-label="Kanban workspace"
                        className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 text-sm text-text-primary"
                        disabled={workspacesQuery.isError || updateWorkspace.isPending}
                        value={selectedWorkspaceId ?? ""}
                        onChange={(event) => {
                          const nextWorkspaceId = event.target.value || null;
                          setSelectedWorkspaceId(nextWorkspaceId);
                          if (selectedPackageId) {
                            updateWorkspace.mutate({ packageId: selectedPackageId, workspaceId: nextWorkspaceId });
                          }
                        }}
                      >
                        <option value="">Choose a Kanban workspace</option>
                        {workspaceOptions.map((workspace) => (
                          <option key={workspace.id ?? workspace.name} value={workspace.id ?? ""}>
                            {workspaceLabel(workspace)}
                          </option>
                        ))}
                      </select>
                    )}
                    <p className="text-xs text-text-tertiary">
                      This choice is saved on the package and used for preview and delivery.
                    </p>
                  </div>
                </div>

              {packageDetail.error_message ? (
                <div className="rounded-md border border-status-red/40 bg-status-red/10 px-3 py-2 text-xs text-status-red">
                  {packageDetail.error_message}
                </div>
              ) : null}

              <div className="space-y-2">
                <div className="text-xs uppercase tracking-wide text-text-tertiary">Cleaned intent</div>
                <p className="whitespace-pre-wrap text-sm text-text-primary">{packageDetail.cleaned_intent}</p>
              </div>

              <div className="space-y-2">
                <div className="text-xs uppercase tracking-wide text-text-tertiary">Prompt steps</div>
                <div className="flex flex-wrap gap-2">
                  {packageDetail.steps.map((step) => (
                    <Button
                      key={step.id}
                      size="sm"
                      variant={step.id === selectedStepId ? "default" : "secondary"}
                      onClick={() => {
                        setSelectedStepId(step.id);
                        setDraft({
                          title: step.title,
                          prompt_markdown: step.prompt_markdown,
                          base_ref: step.base_ref ?? "",
                          agent_id: step.agent_id ?? "",
                          start_in_plan_mode: step.start_in_plan_mode,
                        });
                      }}
                    >
                      {step.step_index}
                      {" "}
                      {step.title}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button disabled={approve.isPending || !selectedPackageId} onClick={() => approve.mutate()} variant="secondary">
                  <Package size={14} />
                  Approve package
                </Button>
                <Button
                  disabled={preview.isPending || !selectedPackageId || !selectedWorkspaceId}
                  onClick={() => preview.mutate()}
                  variant="outline"
                >
                  <Eye size={14} />
                  Preview Kanban payload
                </Button>
                <Button
                  disabled={deliver.isPending || !selectedPackageId || !selectedWorkspaceId}
                  onClick={() => deliver.mutate()}
                >
                  <Send size={14} />
                  Deliver to Kanban
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="py-6 text-sm text-text-tertiary">Select a package to inspect it.</CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Step editor</CardTitle>
            <CardDescription>{selectedStep ? selectedStep.external_task_key : "No step selected."}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {selectedStep && draft ? (
              <>
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-text-tertiary">
                  <span>{isDirty ? "Unsaved changes" : "Saved"}</span>
                  <StatusBadge label={selectedStep.status} tone={statusToneMap[selectedStep.status] ?? "blue"} />
                </div>

                <Input
                  aria-label="Step title"
                  value={draft.title}
                  onChange={(event) => setDraft((current) => (current ? { ...current, title: event.target.value } : current))}
                />
                <Textarea
                  aria-label="Prompt markdown"
                  className="min-h-48"
                  value={draft.prompt_markdown}
                  onChange={(event) =>
                    setDraft((current) => (current ? { ...current, prompt_markdown: event.target.value } : current))
                  }
                />
                <div className="grid gap-3 sm:grid-cols-2">
                  <Input
                    aria-label="Base ref"
                    value={draft.base_ref}
                    onChange={(event) =>
                      setDraft((current) => (current ? { ...current, base_ref: event.target.value } : current))
                    }
                  />
                  <Input
                    aria-label="Agent id"
                    value={draft.agent_id}
                    onChange={(event) =>
                      setDraft((current) => (current ? { ...current, agent_id: event.target.value } : current))
                    }
                  />
                </div>
                <label className="flex items-center gap-2 text-sm text-text-primary">
                  <input
                    type="checkbox"
                    checked={draft.start_in_plan_mode}
                    onChange={(event) =>
                      setDraft((current) =>
                        current ? { ...current, start_in_plan_mode: event.target.checked } : current,
                      )
                    }
                  />
                  Start in plan mode
                </label>
                <div className="flex flex-wrap gap-2">
                  <Button
                    disabled={!selectedStep || !draft || saveStep.isPending || !isDirty}
                    onClick={() => selectedStep && draft && saveStep.mutate({ stepId: selectedStep.id, payload: draft })}
                  >
                    <SquarePen size={14} />
                    Save step
                  </Button>
                  <Button
                    variant="secondary"
                    disabled={!selectedStep}
                    onClick={async () => {
                      if (selectedStep) {
                        if (navigator.clipboard?.writeText) {
                          await navigator.clipboard.writeText(selectedStep.prompt_markdown);
                        }
                        setActionMessage("Prompt markdown copied.");
                      }
                    }}
                  >
                    <Copy size={14} />
                    Copy prompt markdown
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-sm text-text-tertiary">Pick a step to edit its prompt markdown and metadata.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Safe markdown preview</CardTitle>
            <CardDescription>The preview renders text only and never executes HTML.</CardDescription>
          </CardHeader>
          <CardContent>
            <SafeMarkdownPreview
              title={draft?.title ?? selectedStep?.title ?? ""}
              markdown={draft?.prompt_markdown ?? selectedStep?.prompt_markdown ?? ""}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Kanban payload preview</CardTitle>
            <CardDescription>The selected workspace is embedded in preview and delivery.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <pre className="max-h-72 overflow-auto rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-primary">
              {jsonStringify(previewResult ?? deliveryResult ?? packageDetail ?? {})}
            </pre>
            {actionMessage ? <p className="text-xs text-text-secondary">{actionMessage}</p> : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function DeliveriesScreen({
  deliverySelection,
  navigate,
  queryClient,
}: {
  deliverySelection: string | null;
  navigate: (pathname: ScreenPath, search?: Record<string, string | null | undefined>) => void;
  queryClient: ReturnType<typeof useQueryClient>;
}) {
  const deliveriesQuery = useQuery({ queryKey: ["deliveries"], queryFn: listDeliveries, staleTime: 5_000 });
  const deliveries = deliveriesQuery.data?.items ?? [];
  const selectedDeliveryId = deliverySelection ?? deliveries[0]?.id ?? null;
  const deliveryDetailQuery = useQuery({
    queryKey: ["delivery", selectedDeliveryId],
    queryFn: () => getDelivery(selectedDeliveryId ?? ""),
    enabled: Boolean(selectedDeliveryId),
    staleTime: 5_000,
  });
  const retry = useMutation({
    mutationFn: () => retryDelivery(selectedDeliveryId ?? ""),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["deliveries"] }),
        queryClient.invalidateQueries({ queryKey: ["delivery", selectedDeliveryId] }),
        queryClient.invalidateQueries({ queryKey: ["review"] }),
        queryClient.invalidateQueries({ queryKey: ["package"] }),
      ]);
    },
  });

  const selectedDelivery = deliveryDetailQuery.data?.delivery ?? deliveries.find((item) => item.id === selectedDeliveryId) ?? null;

  const refreshDeliveries = async () => {
    await Promise.all([deliveriesQuery.refetch(), deliveryDetailQuery.refetch()]);
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="text-xs uppercase tracking-wide text-text-tertiary">Deliveries</div>
          <Button variant="secondary" size="sm" onClick={refreshDeliveries} disabled={deliveriesQuery.isFetching}>
            <RefreshCw size={14} />
            Refresh
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Package</TableHead>
              <TableHead>Workspace</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {deliveries.map((item) => (
              <TableRow
                key={item.id}
                className={cn(item.id === selectedDeliveryId ? "bg-surface-2" : "")}
                onClick={() => navigate("/deliveries", { delivery: item.id })}
              >
                <TableCell className="space-y-1">
                  <p className="font-medium text-text-primary">{item.source_note_title}</p>
                  <p className="text-xs text-text-tertiary">{item.source_note_path}</p>
                </TableCell>
                <TableCell className="text-xs text-text-secondary">{item.kanban_workspace_id}</TableCell>
                <TableCell>
                  <StatusBadge label={item.status} tone={statusToneMap[item.status] ?? "blue"} />
                </TableCell>
                <TableCell className="text-xs text-text-secondary">{formatTimestamp(item.created_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Card className="h-fit">
        <CardHeader>
          <CardTitle>{selectedDelivery ? selectedDelivery.source_note_title : "Select a delivery"}</CardTitle>
          <CardDescription>{selectedDelivery?.source_note_path ?? "No delivery selected yet."}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {selectedDelivery ? (
            <>
              <div className="grid gap-2 text-text-secondary">
                <div className="flex justify-between gap-4">
                  <span>Status</span>
                  <StatusBadge label={selectedDelivery.status} tone={statusToneMap[selectedDelivery.status] ?? "blue"} />
                </div>
                <div className="flex justify-between gap-4">
                  <span>Workspace</span>
                  <span className="text-text-primary">{selectedDelivery.kanban_workspace_id}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span>Created</span>
                  <span className="text-text-primary">{formatTimestamp(selectedDelivery.created_at)}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span>Delivered</span>
                  <span className="text-text-primary">{formatTimestamp(selectedDelivery.delivered_at)}</span>
                </div>
              </div>

              {selectedDelivery.error_message ? (
                <div className="rounded-md border border-status-red/40 bg-status-red/10 px-3 py-2 text-xs text-status-red">
                  {selectedDelivery.error_message}
                </div>
              ) : null}

              <div className="space-y-2">
                <details className="rounded-md border border-border bg-surface-2 px-3 py-2">
                  <summary className="cursor-pointer text-sm text-text-primary">Request JSON</summary>
                  <pre className="mt-2 overflow-auto text-xs text-text-primary">{jsonStringify(selectedDelivery.request)}</pre>
                </details>
                <details className="rounded-md border border-border bg-surface-2 px-3 py-2">
                  <summary className="cursor-pointer text-sm text-text-primary">Response JSON</summary>
                  <pre className="mt-2 overflow-auto text-xs text-text-primary">{jsonStringify(selectedDelivery.response)}</pre>
                </details>
              </div>

              {selectedDelivery.status === "failed" ? (
                <Button
                  disabled={retry.isPending}
                  onClick={() => retry.mutate()}
                  variant="danger"
                >
                  <RotateCcw size={14} />
                  Retry failed delivery
                </Button>
              ) : null}
            </>
          ) : (
            <p className="text-text-tertiary">Pick a delivery row to inspect request and response JSON.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SettingsScreen() {
  const settings = loadLocalSettings();

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
      <Card>
        <CardHeader>
          <CardTitle>Local config</CardTitle>
          <CardDescription>These values are read-only here. Edit the backend `.env` if they need to change.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div className="grid gap-3 sm:grid-cols-2">
            <SettingRow label="Kanban base URL" value={settings.kanbanBaseUrl} />
            <SettingRow label="Kanban workspace ID" value={settings.kanbanWorkspaceId || "Unset"} />
            <SettingRow label="Vault path" value={settings.vaultPath} />
            <SettingRow label="Watch folder" value={settings.watchFolder} />
          </div>
        </CardContent>
      </Card>

      <Card>
        {/* <CardHeader>
          <CardTitle>Notes</CardTitle>
          <CardDescription>No runtime secrets panel, no admin shell, just the few values this UI can show.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-text-secondary">
          <p>Backend config comes from environment variables.</p>
          <p>There is no in-app save action for these fields.</p>
        </CardContent> */}
      </Card>
    </div>
  );
}

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-surface-2 px-3 py-2">
      <div className="text-xs uppercase tracking-wide text-text-tertiary">{label}</div>
      <div className="mt-1 break-all text-sm text-text-primary">{value}</div>
    </div>
  );
}
