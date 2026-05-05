"use client";

import { UploadCloud, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { UploadedFile } from "@/lib/types";

interface FileUploadProps {
  files: UploadedFile[];
  onFilesSelected: (files: File[]) => void;
  onRemove: (id: string) => void;
  disabled?: boolean;
}

export function FileUpload({ files, onFilesSelected, onRemove, disabled }: FileUploadProps) {
  return (
    <div className="space-y-2">
      <Label>Supporting files</Label>
      <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-muted/35 px-4 py-5 text-center transition-colors hover:bg-muted/60">
        <UploadCloud className="mb-2 h-5 w-5 text-muted-foreground" />
        <span className="text-sm font-medium">Upload documents</span>
        <span className="mt-1 text-xs text-muted-foreground">PDF, DOCX, MD, CSV, or TXT</span>
        <input
          type="file"
          multiple
          className="sr-only"
          disabled={disabled}
          onChange={(event) => onFilesSelected(Array.from(event.currentTarget.files ?? []))}
        />
      </label>
      {files.length > 0 && (
        <div className="space-y-1">
          {files.map((file) => (
            <div key={file.id} className="flex items-center justify-between rounded-md border bg-background px-2 py-1.5">
              <div className="min-w-0">
                <p className="truncate text-xs font-medium">{file.name}</p>
                <p className="text-[11px] text-muted-foreground">{Math.round(file.size / 1024)} KB</p>
              </div>
              <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={() => onRemove(file.id)}>
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
