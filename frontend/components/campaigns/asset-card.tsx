"use client";

import { CheckCircle2, Copy, RefreshCw, ThumbsDown } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import type { CampaignAsset, CampaignChannel } from "@/lib/types";

const CHANNEL_ICONS: Record<string, string> = {
  linkedin: "💼",
  instagram: "📸",
  email: "📧",
  blog: "📝",
  ads: "🎯"
};

const CHANNEL_COLORS: Record<string, string> = {
  linkedin: "bg-blue-50 border-blue-200",
  instagram: "bg-pink-50 border-pink-200",
  email: "bg-amber-50 border-amber-200",
  blog: "bg-emerald-50 border-emerald-200",
  ads: "bg-violet-50 border-violet-200"
};

interface AssetCardProps {
  asset: CampaignAsset;
  campaignId: string;
  conceptRaw: Record<string, unknown>;
  language: string;
  brandProfileId?: string;
  onRegenerate: (assetId: string, channel: CampaignChannel) => Promise<void>;
  onContentChange: (assetId: string, content: string) => void;
}

export function AssetCard({
  asset,
  campaignId,
  conceptRaw,
  language,
  brandProfileId,
  onRegenerate,
  onContentChange
}: AssetCardProps) {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [localContent, setLocalContent] = useState(asset.content);
  const [status, setStatus] = useState<"draft" | "approved" | "needs_revision">(asset.status);

  const channelColor = CHANNEL_COLORS[asset.channel] ?? "bg-neutral-50 border-neutral-200";
  const icon = CHANNEL_ICONS[asset.channel] ?? "📄";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(localContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      await onRegenerate(asset.assetId, asset.channel);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleContentChange = (value: string) => {
    setLocalContent(value);
    onContentChange(asset.assetId, value);
  };

  return (
    <Card className={`border ${channelColor} shadow-none`}>
      <CardHeader className="flex flex-row items-center justify-between gap-3 pb-2 pt-4">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <CardTitle className="text-sm font-semibold">{asset.label}</CardTitle>
        </div>
        <div className="flex items-center gap-1.5">
          <Badge
            variant={status === "approved" ? "success" : "secondary"}
            className="text-xs"
          >
            {status}
          </Badge>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleCopy}
            title="Copy to clipboard"
          >
            <Copy className="h-3.5 w-3.5" />
            <span className="sr-only">{copied ? "Copied" : "Copy"}</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleRegenerate}
            disabled={isRegenerating}
            title="Regenerate this asset"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRegenerating ? "animate-spin" : ""}`} />
            <span className="sr-only">Regenerate</span>
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-4">
        <Textarea
          className="min-h-[140px] resize-y bg-white/80 text-sm leading-relaxed"
          value={localContent}
          onChange={(e) => handleContentChange(e.target.value)}
          placeholder="Content will appear here after generation..."
        />
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            onClick={() => setStatus("approved")}
          >
            <CheckCircle2 className="mr-1 h-3 w-3" />
            Approve
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            onClick={() => setStatus("needs_revision")}
          >
            <ThumbsDown className="mr-1 h-3 w-3" />
            Needs revision
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
