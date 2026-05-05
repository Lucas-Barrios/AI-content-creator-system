"use client";

import { useState } from "react";
import { Loader2, Scissors } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { AppShell } from "@/components/app-shell";
import { SourceInput } from "@/components/repurpose/source-input";
import { FormatSelector } from "@/components/repurpose/format-selector";
import { RepurposeResultView } from "@/components/repurpose/repurpose-result";
import { repurposeContent } from "@/lib/api-client";
import { useWorkspace } from "@/lib/hooks/use-workspace";
import type {
  Language,
  RepurposeFormat,
  RepurposeRequest,
  RepurposeResult,
  SourceType
} from "@/lib/types";

export default function RepurposePage() {
  const { workspace } = useWorkspace();
  const [sourceText, setSourceText] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceType, setSourceType] = useState<SourceType>("blog_post");
  const [targetFormats, setTargetFormats] = useState<RepurposeFormat[]>(["linkedin", "email"]);
  const [language, setLanguage] = useState<Language>("english");
  const [preserveTone, setPreserveTone] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RepurposeResult | null>(null);

  const canSubmit = sourceText.trim().length > 0 && targetFormats.length > 0 && !loading;

  const handleGenerate = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    try {
      const body: RepurposeRequest = {
        organizationId: workspace.organizationId,
        clientId: workspace.clientId,
        projectId: workspace.projectId,
        sourceText: sourceText.trim(),
        sourceTitle: sourceTitle.trim() || "Untitled",
        sourceType,
        targetFormats,
        language,
        preserveTone
      };
      setResult(await repurposeContent(body));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async (outputId: string, format: RepurposeFormat) => {
    if (!result) return;
    const res = await fetch(
      `/api/repurpose/${result.sourceId}/outputs/${outputId}/regenerate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          format,
          extractionRaw: result.extraction.raw,
          language
        })
      }
    );
    if (!res.ok) return;
    const updated = (await res.json()) as { content: string; wordCount: number };
    setResult((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        outputs: prev.outputs.map((o) =>
          o.outputId === outputId
            ? { ...o, content: updated.content, wordCount: updated.wordCount, status: "draft" }
            : o
        )
      };
    });
  };

  const handleContentChange = (outputId: string, content: string) => {
    setResult((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        outputs: prev.outputs.map((o) =>
          o.outputId === outputId ? { ...o, content } : o
        )
      };
    });
  };

  return (
    <AppShell>
    <div className="mx-auto max-w-7xl">
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <Scissors className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">Content Repurposing Engine</h2>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Turn one source asset into multiple platform-ready marketing pieces.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        {/* Left panel — inputs */}
        <div className="space-y-6">
          <SourceInput
            sourceText={sourceText}
            sourceTitle={sourceTitle}
            sourceType={sourceType}
            disabled={loading}
            onSourceTextChange={setSourceText}
            onSourceTitleChange={setSourceTitle}
            onSourceTypeChange={setSourceType}
          />

          <FormatSelector selected={targetFormats} disabled={loading} onChange={setTargetFormats} />

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Language</Label>
              <Select
                value={language}
                onValueChange={(v) => setLanguage(v as Language)}
                disabled={loading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="english">English</SelectItem>
                  <SelectItem value="german">German</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col justify-end space-y-2 pb-0.5">
              <div className="flex items-center gap-2">
                <Switch
                  id="preserve-tone"
                  checked={preserveTone}
                  onCheckedChange={setPreserveTone}
                  disabled={loading}
                />
                <Label htmlFor="preserve-tone" className="cursor-pointer text-sm">
                  Preserve tone
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">Keep original voice &amp; style</p>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button
            className="w-full"
            onClick={handleGenerate}
            disabled={!canSubmit}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Repurposing…
              </>
            ) : (
              <>
                <Scissors className="mr-2 h-4 w-4" />
                Repurpose Content
              </>
            )}
          </Button>
        </div>

        {/* Right panel — results */}
        <div>
          {result ? (
            <RepurposeResultView
              result={result}
              language={language}
              onRegenerate={handleRegenerate}
              onContentChange={handleContentChange}
            />
          ) : (
            <div className="flex h-full min-h-[400px] items-center justify-center rounded-xl border border-dashed bg-muted/20">
              <div className="text-center">
                <Scissors className="mx-auto mb-3 h-8 w-8 text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground">
                  Paste your source content and select formats to get started
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
    </AppShell>
  );
}
