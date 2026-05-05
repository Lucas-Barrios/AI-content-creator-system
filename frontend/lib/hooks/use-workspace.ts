"use client";

import { useEffect, useState } from "react";
import type { WorkspaceSelection } from "@/lib/types";
import { defaultWorkspace, readWorkspace, writeWorkspace } from "@/lib/workspace";

export function useWorkspace() {
  const [workspace, setWorkspaceState] = useState<WorkspaceSelection>(defaultWorkspace);

  useEffect(() => {
    setWorkspaceState(readWorkspace());
  }, []);

  const setWorkspace = (next: WorkspaceSelection) => {
    setWorkspaceState(next);
    writeWorkspace(next);
  };

  const updateWorkspace = <K extends keyof WorkspaceSelection>(key: K, value: WorkspaceSelection[K]) => {
    setWorkspaceState((current) => {
      const next = { ...current, [key]: value };
      writeWorkspace(next);
      return next;
    });
  };

  return { workspace, setWorkspace, updateWorkspace };
}
