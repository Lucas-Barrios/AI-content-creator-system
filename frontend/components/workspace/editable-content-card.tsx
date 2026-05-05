"use client";

import { Copy, Download } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { downloadMarkdown } from "@/lib/api-client";

interface EditableContentCardProps {
  title: string;
  eyebrow: string;
  content: string;
  status?: string;
  onChange?: (content: string) => void;
}

export function EditableContentCard({ title, eyebrow, content, status = "draft", onChange }: EditableContentCardProps) {
  const [value, setValue] = useState(content);

  const updateValue = (next: string) => {
    setValue(next);
    onChange?.(next);
  };

  return (
    <Card className="shadow-soft">
      <CardHeader className="flex flex-row items-start justify-between gap-3 pb-3">
        <div>
          <p className="text-xs font-semibold uppercase text-muted-foreground">{eyebrow}</p>
          <CardTitle className="mt-1 text-base">{title}</CardTitle>
        </div>
        <Badge variant={status === "approved" ? "success" : "outline"}>{status}</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <Textarea className="min-h-56 bg-white leading-6" value={value} onChange={(event) => updateValue(event.target.value)} />
        <div className="flex flex-wrap justify-end gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => navigator.clipboard.writeText(value)} disabled={!value}>
            <Copy className="h-4 w-4" />
            Copy
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => downloadMarkdown(value, `${title.toLowerCase().replace(/\s+/g, "-")}.md`)} disabled={!value}>
            <Download className="h-4 w-4" />
            Markdown
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
