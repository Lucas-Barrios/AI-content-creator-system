import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ContentExtraction } from "@/lib/types";

interface ExtractionCardProps {
  extraction: ContentExtraction;
}

export function ExtractionCard({ extraction }: ExtractionCardProps) {
  return (
    <Card className="border-amber-200 bg-amber-50 shadow-none">
      <CardHeader className="pb-2 pt-4">
        <div className="flex items-center gap-2">
          <span className="text-base">🔍</span>
          <CardTitle className="text-sm font-semibold">AI Content Extraction</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pb-4 text-sm">
        <div>
          <p className="font-medium text-amber-900">{extraction.title}</p>
          <p className="mt-0.5 text-xs italic text-amber-700">{extraction.oneSentenceSummary}</p>
        </div>

        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Core argument</p>
          <p className="text-xs text-amber-900">{extraction.coreArgument}</p>
        </div>

        {extraction.keyPoints.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Key points</p>
            <ul className="space-y-0.5">
              {extraction.keyPoints.map((pt, i) => (
                <li key={i} className="flex gap-1.5 text-xs text-amber-900">
                  <span className="mt-0.5 shrink-0 text-amber-500">•</span>
                  {pt}
                </li>
              ))}
            </ul>
          </div>
        )}

        {extraction.facts.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Facts &amp; stats</p>
            <ul className="space-y-0.5">
              {extraction.facts.map((f, i) => (
                <li key={i} className="flex gap-1.5 text-xs text-amber-900">
                  <span className="mt-0.5 shrink-0 text-amber-500">▸</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}

        {extraction.quotes.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Quotes</p>
            {extraction.quotes.map((q, i) => (
              <blockquote key={i} className="border-l-2 border-amber-400 pl-2 text-xs italic text-amber-800">
                &ldquo;{q}&rdquo;
              </blockquote>
            ))}
          </div>
        )}

        <div className="flex flex-wrap gap-1.5 pt-1">
          <Badge variant="secondary" className="border-amber-300 bg-amber-100 text-amber-800 text-xs">
            Tone: {extraction.tone}
          </Badge>
          {extraction.audienceSignals && (
            <Badge variant="secondary" className="border-amber-300 bg-amber-100 text-amber-800 text-xs">
              Audience: {extraction.audienceSignals}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
