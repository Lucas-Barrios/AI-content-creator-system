"use client";

import { useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { AppShell } from "@/components/app-shell";
import { CampaignForm } from "@/components/campaigns/campaign-form";
import { CampaignResultView } from "@/components/campaigns/campaign-result";
import { generateCampaign } from "@/lib/api-client";
import { useWorkspace } from "@/lib/hooks/use-workspace";
import type { CampaignAsset, CampaignChannel, CampaignResult, Language, KnowledgeBaseSource } from "@/lib/types";

export default function CampaignsPage() {
  const { workspace } = useWorkspace();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CampaignResult | null>(null);

  const handleGenerate = async (form: {
    goal: string;
    offer: string;
    audience: string;
    channels: CampaignChannel[];
    startDate: string;
    endDate: string;
    language: string;
    tone: string;
    kbSource: string;
    extraContext?: string;
  }) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await generateCampaign({
        organizationId: workspace.organizationId,
        clientId: workspace.clientId,
        projectId: workspace.projectId,
        ...form,
        language: form.language as Language,
        kbSource: form.kbSource as KnowledgeBaseSource
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Campaign generation failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async (assetId: string, channel: CampaignChannel) => {
    if (!result) return;

    const response = await fetch(
      `/api/campaigns/${result.campaignId}/assets/${assetId}/regenerate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel,
          conceptRaw: {
            name: result.concept.name,
            concept_summary: result.concept.conceptSummary,
            core_message: result.concept.coreMessage,
            audience_angle: result.concept.audienceAngle,
            channel_strategy: result.concept.channelStrategy,
            content_ideas: result.concept.contentIdeas,
            cta_suggestions: result.concept.ctaSuggestions,
            calendar_draft: result.concept.calendarDraft
          },
          language: "english"
        })
      }
    );

    if (!response.ok) return;

    const updated = (await response.json()) as { assetId: string; content: string; status: string };

    setResult((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        assets: prev.assets.map((a): CampaignAsset =>
          a.assetId === updated.assetId
            ? { ...a, content: updated.content, status: updated.status as CampaignAsset["status"] }
            : a
        )
      };
    });
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">Campaign Generator</p>
          <h2 className="mt-0.5 text-2xl font-semibold tracking-tight">Build a full campaign in minutes</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Provide a brief and the AI generates a concept, per-channel assets, and a content calendar — all editable and regeneratable.
          </p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertTitle>Generation failed</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className={result ? "grid gap-8 lg:grid-cols-[380px_1fr]" : "max-w-xl"}>
          <div>
            <CampaignForm isLoading={isLoading} onSubmit={handleGenerate} />
          </div>

          {isLoading && (
            <div className="space-y-4">
              <Skeleton className="h-7 w-1/3" />
              <Skeleton className="h-4 w-2/3" />
              <div className="grid gap-4 md:grid-cols-2">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-48 w-full rounded-xl" />
                ))}
              </div>
            </div>
          )}

          {result && !isLoading && (
            <CampaignResultView result={result} onRegenerate={handleRegenerate} />
          )}
        </div>
      </div>
    </AppShell>
  );
}
