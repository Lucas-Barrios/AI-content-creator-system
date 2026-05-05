"use client";

import { ExtractionCard } from "./extraction-card";
import { RepurposeAssetCard } from "./repurpose-asset-card";
import type { RepurposeFormat, RepurposeResult } from "@/lib/types";

interface RepurposeResultProps {
  result: RepurposeResult;
  language: string;
  brandProfileId?: string;
  onRegenerate: (outputId: string, format: RepurposeFormat) => Promise<void>;
  onContentChange: (outputId: string, content: string) => void;
}

export function RepurposeResultView({
  result,
  language,
  brandProfileId,
  onRegenerate,
  onContentChange
}: RepurposeResultProps) {
  return (
    <div className="space-y-6">
      <ExtractionCard extraction={result.extraction} />

      <div>
        <h2 className="mb-3 text-sm font-semibold">
          Repurposed outputs
          <span className="ml-1.5 text-muted-foreground font-normal">({result.outputs.length})</span>
        </h2>
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {result.outputs.map((output) => (
            <RepurposeAssetCard
              key={output.outputId}
              output={output}
              sourceId={result.sourceId}
              extractionRaw={result.extraction.raw}
              language={language}
              brandProfileId={brandProfileId}
              onRegenerate={onRegenerate}
              onContentChange={onContentChange}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
