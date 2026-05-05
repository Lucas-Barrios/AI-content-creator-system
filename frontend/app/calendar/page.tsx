"use client";

import { CalendarDays } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { EmptyState } from "@/components/workspace/empty-state";
import { PageHeader } from "@/components/workspace/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listCampaigns } from "@/lib/api-client";
import { useWorkspace } from "@/lib/hooks/use-workspace";
import type { CampaignSummary } from "@/lib/types";

export default function CalendarPage() {
  const { workspace } = useWorkspace();
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listCampaigns(workspace.clientId, workspace.projectId)
      .then((data) => setCampaigns(data.campaigns))
      .catch(() => setCampaigns([]))
      .finally(() => setLoading(false));
  }, [workspace.clientId, workspace.projectId]);

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader
          eyebrow="Content Calendar"
          title="Plan and review campaign timing"
          description="Calendar data is backed by generated campaigns. The next backend step is exposing `content_calendar_items` directly from Supabase."
          icon={CalendarDays}
          badge="Campaign linked"
        />
        <Card>
          <CardHeader>
            <CardTitle>Campaign schedule</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="grid gap-3 md:grid-cols-3">
                <Skeleton className="h-40" />
                <Skeleton className="h-40" />
                <Skeleton className="h-40" />
              </div>
            ) : campaigns.length ? (
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {campaigns.map((campaign) => (
                  <div key={campaign.id} className="rounded-md border bg-white p-4">
                    <p className="font-semibold">{campaign.name}</p>
                    <p className="mt-2 text-sm text-muted-foreground">{campaign.objective}</p>
                    <div className="mt-4 flex justify-between text-xs text-muted-foreground">
                      <span>{campaign.start_date || "No start"}</span>
                      <span>{campaign.end_date || "No end"}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={CalendarDays}
                title="No campaign calendar yet"
                description="Generate a campaign to create campaign records. Calendar-item persistence is ready in the database schema."
              />
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
