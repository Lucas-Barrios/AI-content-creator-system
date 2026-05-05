"use client";

import { RefreshCcw, Send, Square } from "lucide-react";
import { useChat } from "@ai-sdk/react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

export function ChatPanel() {
  const { messages, input, handleInputChange, handleSubmit, isLoading, error, reload, stop } = useChat({
    api: "/api/chat",
    streamProtocol: "text"
  });

  return (
    <Card className="h-full shadow-soft">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">AI assistant</CardTitle>
        <p className="text-sm text-muted-foreground">Edit, improve, or transform content after generation.</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && (
          <Alert variant="destructive">
            <AlertTitle>Chat unavailable</AlertTitle>
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        )}
        <ScrollArea className="h-72 rounded-lg border bg-white">
          <div className="space-y-3 p-3">
            {messages.length === 0 ? (
              <p className="text-sm text-muted-foreground">Ask for edits, shorter variants, or channel-specific repurposing.</p>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "rounded-lg px-3 py-2 text-sm leading-6",
                    message.role === "user" ? "ml-8 bg-primary text-primary-foreground" : "mr-8 bg-muted"
                  )}
                >
                  {message.content}
                </div>
              ))
            )}
          </div>
        </ScrollArea>
        <form className="flex gap-2" onSubmit={handleSubmit}>
          <Input value={input} onChange={handleInputChange} placeholder="Ask for a revision or campaign variant..." />
          {isLoading ? (
            <Button type="button" variant="outline" size="icon" onClick={stop}>
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button type="submit" size="icon" disabled={!input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          )}
          <Button type="button" variant="outline" size="icon" disabled={!messages.length || isLoading} onClick={() => reload()}>
            <RefreshCcw className="h-4 w-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
