"use client";

import Link from "next/link";
import type { Route } from "next";
import { Activity, BookOpen, CalendarDays, FolderKanban, Megaphone, Scissors } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/workspace/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getBackendHealth, listCampaigns } from "@/lib/api-client";
import { useWorkspace } from "@/lib/hooks/use-workspace";
import type { CampaignSummary } from "@/lib/types";

export default function DashboardPage() {
  const { workspace } = useWorkspace();
  const [health, setHealth] = useState<"loading" | "ok" | "error">("loading");
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);

  useEffect(() => {
    getBackendHealth().then(() => setHealth("ok")).catch(() => setHealth("error"));
  }, []);

  useEffect(() => {
    setLoadingCampaigns(true);
    listCampaigns(workspace.clientId, workspace.projectId)
      .then((data) => setCampaigns(data.campaigns))
      .catch(() => setCampaigns([]))
      .finally(() => setLoadingCampaigns(false));
  }, [workspace.clientId, workspace.projectId]);

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader
          eyebrow="Dashboard"
          title="Content operations at a glance"
          description="Monitor backend readiness, jump into key workflows, and review recent API-backed campaign activity for the selected client/project."
          icon={Activity}
          badge={health === "ok" ? "Backend online" : health === "loading" ? "Checking backend" : "Backend unavailable"}
        />

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {([
            { label: "Knowledge sources", value: "RAG ready", href: "/knowledge-base", icon: BookOpen },
            { label: "Campaigns", value: String(campaigns.length), href: "/campaigns", icon: Megaphone },
            { label: "Repurposing", value: "Multi-format", href: "/repurpose", icon: Scissors },
            { label: "Calendar", value: "Planned assets", href: "/calendar", icon: CalendarDays }
          ] satisfies Array<{ label: string; value: string; href: Route; icon: typeof BookOpen }>).map((item) => (
            <Card key={item.label}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm text-muted-foreground">{item.label}</CardTitle>
                  <item.icon className="h-4 w-4 text-primary" />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold">{item.value}</p>
                <Button asChild variant="ghost" size="sm" className="mt-3 px-0">
                  <Link href={item.href}>Open</Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent campaigns</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {loadingCampaigns ? (
              <>
                <Skeleton className="h-14 w-full" />
                <Skeleton className="h-14 w-full" />
              </>
            ) : campaigns.length ? (
              campaigns.slice(0, 5).map((campaign) => (
                <div key={campaign.id} className="flex items-center justify-between rounded-md border p-3">
                  <div>
                    <p className="font-medium">{campaign.name}</p>
                    <p className="text-sm text-muted-foreground">{campaign.objective}</p>
                  </div>
                  <Button asChild variant="outline" size="sm">
                    <Link href="/campaigns">View</Link>
                  </Button>
                </div>
              ))
            ) : (
              <div className="rounded-md border border-dashed p-6 text-center">
                <FolderKanban className="mx-auto mb-2 h-7 w-7 text-muted-foreground/60" />
                <p className="font-medium">No campaigns returned for this workspace</p>
                <p className="mt-1 text-sm text-muted-foreground">Generate a campaign once Supabase credentials and schema are active.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
