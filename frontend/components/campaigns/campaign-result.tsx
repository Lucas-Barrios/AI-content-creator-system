"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AssetCard } from "@/components/campaigns/asset-card";
import type { CampaignAsset, CampaignChannel, CampaignResult } from "@/lib/types";

interface CampaignResultProps {
  result: CampaignResult;
  onRegenerate: (assetId: string, channel: CampaignChannel) => Promise<void>;
}

export function CampaignResultView({ result, onRegenerate }: CampaignResultProps) {
  const { concept, assets } = result;
  const [assetContents, setAssetContents] = useState<Record<string, string>>(
    Object.fromEntries(assets.map((a) => [a.assetId, a.content]))
  );

  const handleContentChange = (assetId: string, content: string) => {
    setAssetContents((prev) => ({ ...prev, [assetId]: content }));
  };

  const conceptRaw = {
    name: concept.name,
    concept_summary: concept.conceptSummary,
    core_message: concept.coreMessage,
    audience_angle: concept.audienceAngle,
    channel_strategy: concept.channelStrategy,
    content_ideas: concept.contentIdeas,
    cta_suggestions: concept.ctaSuggestions,
    calendar_draft: concept.calendarDraft
  };

  return (
    <div className="space-y-6">
      {/* Campaign header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">{concept.name}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{concept.conceptSummary}</p>
        </div>
        <Badge variant="success">Generated</Badge>
      </div>

      <Tabs defaultValue="strategy">
        <TabsList className="mb-4">
          <TabsTrigger value="strategy">Strategy</TabsTrigger>
          <TabsTrigger value="assets">Assets ({assets.length})</TabsTrigger>
          <TabsTrigger value="ideas">Content ideas ({concept.contentIdeas.length})</TabsTrigger>
          <TabsTrigger value="calendar">Calendar</TabsTrigger>
        </TabsList>

        {/* Strategy tab */}
        <TabsContent value="strategy" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="shadow-none">
              <CardHeader className="pb-2 pt-4">
                <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                  Core message
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed">{concept.coreMessage}</p>
              </CardContent>
            </Card>

            <Card className="shadow-none">
              <CardHeader className="pb-2 pt-4">
                <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                  Audience angle
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed">{concept.audienceAngle}</p>
              </CardContent>
            </Card>
          </div>

          <Card className="shadow-none">
            <CardHeader className="pb-2 pt-4">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Channel strategy
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">{concept.channelStrategy}</p>
            </CardContent>
          </Card>

          {concept.ctaSuggestions.length > 0 && (
            <Card className="shadow-none">
              <CardHeader className="pb-2 pt-4">
                <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                  CTA suggestions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1.5">
                  {concept.ctaSuggestions.map((cta, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <span className="text-primary">→</span>
                      {cta}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Assets tab */}
        <TabsContent value="assets">
          <div className="grid gap-4 md:grid-cols-2">
            {assets.map((asset) => (
              <AssetCard
                key={asset.assetId}
                asset={{ ...asset, content: assetContents[asset.assetId] ?? asset.content }}
                campaignId={result.campaignId}
                conceptRaw={conceptRaw}
                language="english"
                onRegenerate={onRegenerate}
                onContentChange={handleContentChange}
              />
            ))}
          </div>
        </TabsContent>

        {/* Content ideas tab */}
        <TabsContent value="ideas">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {concept.contentIdeas.map((idea) => (
              <Card key={idea.id} className="shadow-none">
                <CardContent className="p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <Badge variant="outline" className="text-xs capitalize">
                      {idea.channel}
                    </Badge>
                    <span className="text-xs text-muted-foreground">Week {idea.week}</span>
                  </div>
                  <p className="mb-1 text-sm font-semibold leading-snug">{idea.title}</p>
                  <p className="text-xs text-muted-foreground">
                    <span className="font-medium">Format:</span> {idea.format}
                  </p>
                  <p className="mt-2 text-xs italic text-muted-foreground">&ldquo;{idea.hook}&rdquo;</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Calendar tab */}
        <TabsContent value="calendar">
          <Card className="shadow-none">
            <CardContent className="p-0">
              <ScrollArea className="h-[420px]">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-muted/60">
                    <tr>
                      <th className="px-4 py-2.5 text-left font-semibold">Week</th>
                      <th className="px-4 py-2.5 text-left font-semibold">Day</th>
                      <th className="px-4 py-2.5 text-left font-semibold">Channel</th>
                      <th className="px-4 py-2.5 text-left font-semibold">Content</th>
                      <th className="px-4 py-2.5 text-left font-semibold">Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {concept.calendarDraft.map((entry, i) => (
                      <tr key={i} className="border-t hover:bg-muted/30">
                        <td className="px-4 py-2.5 font-medium">{entry.week}</td>
                        <td className="px-4 py-2.5 text-muted-foreground">{entry.day}</td>
                        <td className="px-4 py-2.5 capitalize">
                          <Badge variant="secondary" className="text-xs">
                            {entry.channel}
                          </Badge>
                        </td>
                        <td className="px-4 py-2.5 max-w-xs truncate">{entry.title}</td>
                        <td className="px-4 py-2.5 text-muted-foreground capitalize">{entry.content_type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
