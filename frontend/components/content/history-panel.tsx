"use client";

import { History } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { HistoryItem } from "@/lib/types";

export function HistoryPanel({ history }: { history: HistoryItem[] }) {
  return (
    <Card className="h-full shadow-soft">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="h-4 w-4" />
          Recent generations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-72">
          <div className="space-y-2">
            {history.length === 0 ? (
              <p className="text-sm text-muted-foreground">Successful generations will be stored locally in this browser.</p>
            ) : (
              history.map((item) => (
                <div key={item.id} className="rounded-md border bg-white p-3">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-semibold">{item.request.topic}</p>
                    <Badge variant="outline">{item.request.contentType}</Badge>
                  </div>
                  <p className="line-clamp-2 text-xs leading-5 text-muted-foreground">{item.response.content}</p>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
