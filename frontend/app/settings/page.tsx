import { Settings } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/workspace/page-header";
import { WorkspaceIdPanel } from "@/components/workspace/workspace-id-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-6">
        <PageHeader
          eyebrow="Settings"
          title="Workspace and integration settings"
          description="Review the current integration state and edit tenant identifiers used by API-backed workflows."
          icon={Settings}
          badge="Configuration"
        />
        <WorkspaceIdPanel />
        <Card>
          <CardHeader>
            <CardTitle>Integration status</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            <div className="rounded-md border p-4">
              <div className="flex items-center justify-between">
                <p className="font-medium">Python API</p>
                <Badge variant="outline">Required</Badge>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">Configured through `PYTHON_API_BASE_URL`.</p>
            </div>
            <div className="rounded-md border p-4">
              <div className="flex items-center justify-between">
                <p className="font-medium">Supabase</p>
                <Badge variant="outline">RLS ready</Badge>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">Frontend uses publishable keys; backend uses service-role credentials only on the server.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
