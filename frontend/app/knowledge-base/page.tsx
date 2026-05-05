"use client";

import { BookOpen, Loader2, Search, Upload } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/workspace/page-header";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ingestKnowledgeFile, ingestKnowledgeText, searchKnowledge } from "@/lib/api-client";
import { useWorkspace } from "@/lib/hooks/use-workspace";
import type { KnowledgeIngestionResponse, KnowledgeMatch, KnowledgeSourceKind, MarketingContentType } from "@/lib/types";

export default function KnowledgeBasePage() {
  const { workspace } = useWorkspace();
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [sourceKind, setSourceKind] = useState<KnowledgeSourceKind>("brand");
  const [contentType, setContentType] = useState<MarketingContentType>("blog");
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [result, setResult] = useState<KnowledgeIngestionResponse | null>(null);
  const [matches, setMatches] = useState<KnowledgeMatch[]>([]);
  const [error, setError] = useState<string | null>(null);

  const ingest = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = file
        ? await ingestKnowledgeFile({
            organizationId: workspace.organizationId,
            clientId: workspace.clientId,
            projectId: workspace.projectId,
            title: title || file.name,
            sourceKind,
            contentType,
            language: "english",
            channel: contentType === "newsletter" ? "newsletter" : contentType === "social" ? "linkedin" : "blog",
            file
          })
        : await ingestKnowledgeText({
            organizationId: workspace.organizationId,
            clientId: workspace.clientId,
            projectId: workspace.projectId,
            title,
            text,
            sourceKind,
            contentType,
            language: "english",
            channel: contentType === "newsletter" ? "newsletter" : contentType === "social" ? "linkedin" : "blog"
          });
      setResult(response);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Knowledge ingestion failed.");
    } finally {
      setLoading(false);
    }
  };

  const runSearch = async () => {
    setSearching(true);
    setError(null);
    try {
      const response = await searchKnowledge({
        query,
        clientId: workspace.clientId,
        projectId: workspace.projectId,
        contentType,
        language: "english",
        matchCount: 6
      });
      setMatches(response.matches);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Knowledge search failed.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader
          eyebrow="Knowledge Base"
          title="Ingest and retrieve client knowledge"
          description="Upload files or paste source text. The backend extracts text, chunks it, embeds it, and stores vectors in Supabase pgvector."
          icon={BookOpen}
          badge="RAG connected"
        />
        {error && (
          <Alert variant="destructive">
            <AlertTitle>Action needed</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <div className="grid gap-5 lg:grid-cols-[420px_1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Add source</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Title</Label>
                <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Brand guidelines, homepage copy, case study..." />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Source type</Label>
                  <Select value={sourceKind} onValueChange={(value) => setSourceKind(value as KnowledgeSourceKind)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {["brand", "product", "audience", "market", "competitor", "campaign", "policy", "other"].map((item) => (
                        <SelectItem key={item} value={item}>{item}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Content type</Label>
                  <Select value={contentType} onValueChange={(value) => setContentType(value as MarketingContentType)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {["blog", "social", "email", "newsletter", "ad", "landing_page", "program", "other"].map((item) => (
                        <SelectItem key={item} value={item}>{item}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Upload PDF, DOCX, TXT, or Markdown</Label>
                <Input type="file" accept=".pdf,.docx,.txt,.md,.markdown" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
              </div>
              <div className="space-y-2">
                <Label>Pasted source text</Label>
                <Textarea className="min-h-44 bg-white" value={text} onChange={(event) => setText(event.target.value)} placeholder="Paste website text or existing marketing copy..." />
              </div>
              <Button className="w-full" onClick={ingest} disabled={loading || (!file && (!title.trim() || !text.trim()))}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                Ingest source
              </Button>
              {result && (
                <div className="rounded-md border bg-muted/35 p-3 text-sm">
                  <p className="font-semibold">{result.message}</p>
                  <p className="mt-1 text-muted-foreground">{result.chunkCount} chunks, {result.embeddingCount} embeddings</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Search retrieval context</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search brand voice, proof points, campaign facts..." />
                <Button onClick={runSearch} disabled={searching || !query.trim()}>
                  {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                  Search
                </Button>
              </div>
              {searching ? (
                <div className="space-y-3">
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                </div>
              ) : matches.length ? (
                <div className="space-y-3">
                  {matches.map((match) => (
                    <div key={match.chunk_id} className="rounded-md border bg-white p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-medium">{match.title}</p>
                        <span className="text-xs text-muted-foreground">{Math.round(match.similarity * 100)}% match</span>
                      </div>
                      <p className="mt-2 line-clamp-4 text-sm leading-6 text-muted-foreground">{match.content}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-md border border-dashed p-8 text-center text-sm text-muted-foreground">
                  Search results from Supabase pgvector will appear here.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
