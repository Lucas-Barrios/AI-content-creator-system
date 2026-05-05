"use client";

import { useRef, useState } from "react";
import { FileText, UploadCloud, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { SourceType } from "@/lib/types";

const SOURCE_TYPES: { value: SourceType; label: string }[] = [
  { value: "blog_post", label: "Blog Post" },
  { value: "transcript", label: "Transcript" },
  { value: "webinar_notes", label: "Webinar Notes" },
  { value: "article", label: "Article" },
  { value: "social_post", label: "Social Post" },
  { value: "document", label: "Document" },
  { value: "other", label: "Other" }
];

interface SourceInputProps {
  sourceText: string;
  sourceTitle: string;
  sourceType: SourceType;
  disabled?: boolean;
  onSourceTextChange: (v: string) => void;
  onSourceTitleChange: (v: string) => void;
  onSourceTypeChange: (v: SourceType) => void;
}

export function SourceInput({
  sourceText,
  sourceTitle,
  sourceType,
  disabled,
  onSourceTextChange,
  onSourceTitleChange,
  onSourceTypeChange
}: SourceInputProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (file: File) => {
    const plainTypes = ["text/plain", "text/markdown", "text/csv"];
    if (plainTypes.includes(file.type) || file.name.match(/\.(txt|md|csv)$/i)) {
      const text = await file.text();
      onSourceTextChange(text);
      onSourceTitleChange(file.name.replace(/\.[^.]+$/, ""));
      setFileName(file.name);
      return;
    }

    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/api/repurpose/extract-file", { method: "POST", body: form });
      if (!res.ok) throw new Error("Extraction failed");
      const data = (await res.json()) as { text: string; title?: string };
      onSourceTextChange(data.text ?? "");
      onSourceTitleChange(data.title ?? file.name.replace(/\.[^.]+$/, ""));
      setFileName(file.name);
    } catch {
      // leave existing text unchanged on error
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) void handleFile(file);
  };

  const clearFile = () => {
    setFileName(null);
    onSourceTextChange("");
    onSourceTitleChange("");
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-[1fr_auto] gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="source-title">Source title</Label>
          <input
            id="source-title"
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            placeholder="e.g. Q1 Product Launch Blog"
            value={sourceTitle}
            disabled={disabled}
            onChange={(e) => onSourceTitleChange(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label>Content type</Label>
          <Select value={sourceType} onValueChange={(v) => onSourceTypeChange(v as SourceType)} disabled={disabled}>
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SOURCE_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {fileName ? (
        <div className="flex items-center gap-2 rounded-md border bg-muted/30 px-3 py-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="min-w-0 flex-1 truncate text-sm">{fileName}</span>
          {uploading && <span className="text-xs text-muted-foreground">extracting…</span>}
          <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={clearFile}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      ) : (
        <label
          className="flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-muted/35 px-4 py-4 text-center transition-colors hover:bg-muted/60"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <UploadCloud className="mb-2 h-5 w-5 text-muted-foreground" />
          <span className="text-sm font-medium">Upload a file</span>
          <span className="mt-0.5 text-xs text-muted-foreground">PDF, DOCX, TXT, or MD — or paste text below</span>
          <input
            ref={fileRef}
            type="file"
            className="sr-only"
            accept=".pdf,.docx,.doc,.txt,.md,.csv"
            disabled={disabled}
            onChange={(e) => {
              const file = e.currentTarget.files?.[0];
              if (file) void handleFile(file);
            }}
          />
        </label>
      )}

      <div className="space-y-1.5">
        <Label htmlFor="source-text">Source text</Label>
        <Textarea
          id="source-text"
          className="min-h-[200px] resize-y font-mono text-xs leading-relaxed"
          placeholder="Paste or type your source content here…"
          value={sourceText}
          disabled={disabled || uploading}
          onChange={(e) => onSourceTextChange(e.target.value)}
        />
        <p className="text-right text-xs text-muted-foreground">
          {sourceText.trim().split(/\s+/).filter(Boolean).length} words
        </p>
      </div>
    </div>
  );
}
