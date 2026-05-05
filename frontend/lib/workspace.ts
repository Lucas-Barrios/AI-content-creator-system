import type { WorkspaceSelection } from "@/lib/types";

export const workspaceStorageKey = "ai-marketing-workspace";

export const defaultWorkspace: WorkspaceSelection = {
  organizationId: "00000000-0000-0000-0000-000000000001",
  clientId: "00000000-0000-0000-0000-000000000002",
  projectId: "00000000-0000-0000-0000-000000000003",
  clientName: "Demo client",
  projectName: "Marketing workspace"
};

export function readWorkspace(): WorkspaceSelection {
  if (typeof window === "undefined") return defaultWorkspace;
  const raw = window.localStorage.getItem(workspaceStorageKey);
  if (!raw) return defaultWorkspace;
  try {
    return { ...defaultWorkspace, ...(JSON.parse(raw) as Partial<WorkspaceSelection>) };
  } catch {
    window.localStorage.removeItem(workspaceStorageKey);
    return defaultWorkspace;
  }
}

export function writeWorkspace(workspace: WorkspaceSelection) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(workspaceStorageKey, JSON.stringify(workspace));
}
