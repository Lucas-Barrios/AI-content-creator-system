"use client";

import { Loader2 } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { CampaignChannel, CampaignRequest, Language } from "@/lib/types";
import { cn } from "@/lib/utils";

const CHANNELS: Array<{ value: CampaignChannel; label: string; icon: string }> = [
  { value: "linkedin", label: "LinkedIn", icon: "💼" },
  { value: "instagram", label: "Instagram", icon: "📸" },
  { value: "email", label: "Email", icon: "📧" },
  { value: "blog", label: "Blog", icon: "📝" },
  { value: "ads", label: "Ads", icon: "🎯" }
];

const TONE_OPTIONS = ["Academic", "Formal", "Professional", "Friendly", "Conversational"];
const AUDIENCE_OPTIONS = [
  "SME owners",
  "Marketing managers",
  "Prospective students",
  "B2B decision-makers",
  "Young professionals",
  "Enterprise buyers",
  "General consumers"
];

function todayIso() {
  return new Date().toISOString().split("T")[0];
}

function weeksFromTodayIso(weeks: number) {
  const d = new Date();
  d.setDate(d.getDate() + weeks * 7);
  return d.toISOString().split("T")[0];
}

const defaultForm: Omit<CampaignRequest, "organizationId" | "clientId" | "projectId"> = {
  goal: "",
  offer: "",
  audience: "SME owners",
  channels: ["linkedin", "email"],
  startDate: todayIso(),
  endDate: weeksFromTodayIso(4),
  language: "english",
  tone: "Professional",
  kbSource: "hybrid",
  extraContext: ""
};

interface CampaignFormProps {
  isLoading: boolean;
  onSubmit: (form: typeof defaultForm) => void;
}

export function CampaignForm({ isLoading, onSubmit }: CampaignFormProps) {
  const [form, setForm] = useState(defaultForm);

  const set = <K extends keyof typeof defaultForm>(key: K, value: (typeof defaultForm)[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const toggleChannel = (ch: CampaignChannel) => {
    set(
      "channels",
      form.channels.includes(ch) ? form.channels.filter((c) => c !== ch) : [...form.channels, ch]
    );
  };

  const canSubmit = form.goal.trim() && form.offer.trim() && form.channels.length > 0;

  return (
    <Card className="shadow-soft">
      <CardHeader>
        <CardTitle>Campaign brief</CardTitle>
        <CardDescription>
          Fill in the brief below — the AI will generate a full campaign concept, channel assets, and a content calendar in one run.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Goal */}
        <div className="space-y-1.5">
          <Label htmlFor="goal">Campaign goal *</Label>
          <Input
            id="goal"
            placeholder="e.g. Generate 50 qualified leads for our new HR software in Q3"
            value={form.goal}
            onChange={(e) => set("goal", e.target.value)}
          />
        </div>

        {/* Offer */}
        <div className="space-y-1.5">
          <Label htmlFor="offer">Offer / service *</Label>
          <Input
            id="offer"
            placeholder="e.g. HR automation software with a 14-day free trial"
            value={form.offer}
            onChange={(e) => set("offer", e.target.value)}
          />
        </div>

        {/* Audience */}
        <div className="space-y-1.5">
          <Label>Target audience</Label>
          <Select value={form.audience} onValueChange={(v) => set("audience", v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {AUDIENCE_OPTIONS.map((a) => (
                <SelectItem key={a} value={a}>
                  {a}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Channels */}
        <div className="space-y-1.5">
          <Label>Channels *</Label>
          <div className="flex flex-wrap gap-2">
            {CHANNELS.map((ch) => (
              <button
                key={ch.value}
                type="button"
                onClick={() => toggleChannel(ch.value)}
                className={cn(
                  "flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
                  form.channels.includes(ch.value)
                    ? "border-primary bg-primary text-white"
                    : "border-border bg-background hover:bg-muted"
                )}
              >
                <span>{ch.icon}</span>
                {ch.label}
              </button>
            ))}
          </div>
          {form.channels.length === 0 && (
            <p className="text-xs text-destructive">Select at least one channel.</p>
          )}
        </div>

        {/* Dates */}
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="start-date">Start date</Label>
            <Input
              id="start-date"
              type="date"
              value={form.startDate}
              onChange={(e) => set("startDate", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="end-date">End date</Label>
            <Input
              id="end-date"
              type="date"
              value={form.endDate}
              onChange={(e) => set("endDate", e.target.value)}
            />
          </div>
        </div>

        {/* Language + Tone */}
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Language</Label>
            <Select value={form.language} onValueChange={(v) => set("language", v as Language)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="english">🇬🇧 English</SelectItem>
                <SelectItem value="german">🇩🇪 German</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Tone</Label>
            <Select value={form.tone} onValueChange={(v) => set("tone", v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TONE_OPTIONS.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Extra context */}
        <div className="space-y-1.5">
          <Label htmlFor="extra-context">Additional context (optional)</Label>
          <Textarea
            id="extra-context"
            className="min-h-20 resize-y text-sm"
            placeholder="Paste brand guidelines, competitor notes, key stats, or any context the AI should use..."
            value={form.extraContext}
            onChange={(e) => set("extraContext", e.target.value)}
          />
        </div>

        <Button
          type="button"
          size="lg"
          className="w-full"
          disabled={isLoading || !canSubmit}
          onClick={() => onSubmit(form)}
        >
          {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          {isLoading ? "Generating campaign…" : "✨ Generate full campaign"}
        </Button>
      </CardContent>
    </Card>
  );
}
