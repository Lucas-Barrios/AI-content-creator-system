import { Building2 } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/workspace/page-header";
import { WorkspaceIdPanel } from "@/components/workspace/workspace-id-panel";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ClientsPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-6">
        <PageHeader
          eyebrow="Clients & Projects"
          title="Select the workspace context"
          description="The current product uses explicit organization, client, and project IDs until Supabase Auth and workspace membership screens are wired."
          icon={Building2}
          badge="Tenant scoped"
        />
        <WorkspaceIdPanel />
        <Card>
          <CardHeader>
            <CardTitle>Next database-backed step</CardTitle>
            <CardDescription>Once auth is active, this page should read `clients` and `projects` from Supabase using RLS.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            {["organizations", "clients", "projects"].map((table) => (
              <div key={table} className="rounded-md border bg-muted/30 p-3">
                <p className="text-sm font-semibold">{table}</p>
                <p className="mt-1 text-xs text-muted-foreground">Ready in the Supabase schema.</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
