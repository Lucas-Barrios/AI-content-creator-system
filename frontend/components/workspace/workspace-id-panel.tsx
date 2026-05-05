"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useWorkspace } from "@/lib/hooks/use-workspace";

export function WorkspaceIdPanel() {
  const { workspace, updateWorkspace } = useWorkspace();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Client/project IDs</CardTitle>
        <CardDescription>These IDs are sent to the backend so generation, campaigns, and RAG retrieval stay tenant-scoped.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-3">
        <div className="space-y-2">
          <Label>Organization ID</Label>
          <Input value={workspace.organizationId} onChange={(event) => updateWorkspace("organizationId", event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Client ID</Label>
          <Input value={workspace.clientId} onChange={(event) => updateWorkspace("clientId", event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Project ID</Label>
          <Input value={workspace.projectId} onChange={(event) => updateWorkspace("projectId", event.target.value)} />
        </div>
      </CardContent>
    </Card>
  );
}
