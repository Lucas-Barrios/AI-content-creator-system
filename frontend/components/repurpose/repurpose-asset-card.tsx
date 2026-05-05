"use client";

import { CheckCircle2, Copy, RefreshCw, ThumbsDown } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import type { RepurposedOutput, RepurposeFormat } from "@/lib/types";

const FORMAT_ICONS: Record<string, string> = {
  linkedin: "💼",
  instagram: "📸",
  email: "📧",
  blog_summary: "📝",
  ad_copy: "🎯",
  landing_page: "🖥️",
  video_script: "🎬"
};

const FORMAT_COLORS: Record<string, string> = {
  linkedin: "bg-blue-50 border-blue-200",
  instagram: "bg-pink-50 border-pink-200",
  email: "bg-amber-50 border-amber-200",
  blog_summary: "bg-emerald-50 border-emerald-200",
  ad_copy: "bg-violet-50 border-violet-200",
  landing_page: "bg-cyan-50 border-cyan-200",
  video_script: "bg-rose-50 border-rose-200"
};

interface RepurposeAssetCardProps {
  output: RepurposedOutput;
  sourceId: string;
  extractionRaw: Record<string, unknown>;
  language: string;
  brandProfileId?: string;
  onRegenerate: (outputId: string, format: RepurposeFormat) => Promise<void>;
  onContentChange: (outputId: string, content: string) => void;
}

export function RepurposeAssetCard({
  output,
  extractionRaw,
  onRegenerate,
  onContentChange
}: RepurposeAssetCardProps) {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [localContent, setLocalContent] = useState(output.content);
  const [status, setStatus] = useState<"draft" | "approved" | "needs_revision">(output.status);

  const colorClass = FORMAT_COLORS[output.format] ?? "bg-neutral-50 border-neutral-200";
  const icon = FORMAT_ICONS[output.format] ?? "📄";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(localContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      await onRegenerate(output.outputId, output.format as RepurposeFormat);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleContentChange = (value: string) => {
    setLocalContent(value);
    onContentChange(output.outputId, value);
  };

  const wordCount = localContent.trim().split(/\s+/).filter(Boolean).length;

  return (
    <Card className={`border ${colorClass} shadow-none`}>
      <CardHeader className="flex flex-row items-center justify-between gap-3 pb-2 pt-4">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <CardTitle className="text-sm font-semibold">{output.label}</CardTitle>
        </div>
        <div className="flex items-center gap-1.5">
          <Badge variant="secondary" className="text-[10px]">
            {wordCount}w
          </Badge>
          <Badge variant={status === "approved" ? "success" : "secondary"} className="text-xs">
            {status}
          </Badge>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleCopy} title="Copy">
            <Copy className="h-3.5 w-3.5" />
            <span className="sr-only">{copied ? "Copied" : "Copy"}</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleRegenerate}
            disabled={isRegenerating}
            title="Regenerate"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRegenerating ? "animate-spin" : ""}`} />
            <span className="sr-only">Regenerate</span>
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-4">
        <Textarea
          className="min-h-[150px] resize-y bg-white/80 text-sm leading-relaxed"
          value={localContent}
          onChange={(e) => handleContentChange(e.target.value)}
          placeholder="Repurposed content will appear here…"
        />
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setStatus("approved")}>
            <CheckCircle2 className="mr-1 h-3 w-3" />
            Approve
          </Button>
          <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setStatus("needs_revision")}>
            <ThumbsDown className="mr-1 h-3 w-3" />
            Needs revision
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
