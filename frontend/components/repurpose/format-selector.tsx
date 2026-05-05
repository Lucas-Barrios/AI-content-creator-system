"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import type { RepurposeFormat } from "@/lib/types";

interface FormatMeta {
  label: string;
  icon: string;
  description: string;
}

const FORMAT_META: Record<RepurposeFormat, FormatMeta> = {
  linkedin: {
    label: "LinkedIn Post",
    icon: "💼",
    description: "Professional post optimised for engagement"
  },
  instagram: {
    label: "Instagram Caption",
    icon: "📸",
    description: "Visual-first caption with hashtags"
  },
  email: {
    label: "Email Newsletter",
    icon: "📧",
    description: "Subject line + body with clear CTA"
  },
  blog_summary: {
    label: "Blog Summary",
    icon: "📝",
    description: "SEO-friendly condensed blog version"
  },
  ad_copy: {
    label: "Ad Copy",
    icon: "🎯",
    description: "Headline + body for paid ads"
  },
  landing_page: {
    label: "Landing Page Section",
    icon: "🖥️",
    description: "Hero/feature block with CTA"
  },
  video_script: {
    label: "Short Video Script",
    icon: "🎬",
    description: "60-second timed script with visual cues"
  }
};

const ALL_FORMATS = Object.keys(FORMAT_META) as RepurposeFormat[];

interface FormatSelectorProps {
  selected: RepurposeFormat[];
  disabled?: boolean;
  onChange: (formats: RepurposeFormat[]) => void;
}

export function FormatSelector({ selected, disabled, onChange }: FormatSelectorProps) {
  const toggle = (fmt: RepurposeFormat) => {
    onChange(
      selected.includes(fmt) ? selected.filter((f) => f !== fmt) : [...selected, fmt]
    );
  };

  const toggleAll = () => {
    onChange(selected.length === ALL_FORMATS.length ? [] : [...ALL_FORMATS]);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label>Output formats</Label>
        <button
          type="button"
          className="text-xs text-primary underline-offset-2 hover:underline disabled:opacity-50"
          disabled={disabled}
          onClick={toggleAll}
        >
          {selected.length === ALL_FORMATS.length ? "Deselect all" : "Select all"}
        </button>
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {ALL_FORMATS.map((fmt) => {
          const meta = FORMAT_META[fmt];
          const checked = selected.includes(fmt);
          return (
            <label
              key={fmt}
              className={`flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2.5 transition-colors ${
                checked
                  ? "border-primary/40 bg-primary/5"
                  : "border-border bg-background hover:bg-muted/40"
              } ${disabled ? "pointer-events-none opacity-50" : ""}`}
            >
              <Checkbox
                id={`fmt-${fmt}`}
                checked={checked}
                disabled={disabled}
                onCheckedChange={() => toggle(fmt)}
                className="mt-0.5"
              />
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span>{meta.icon}</span>
                  <span className="text-sm font-medium">{meta.label}</span>
                </div>
                <p className="text-xs text-muted-foreground">{meta.description}</p>
              </div>
            </label>
          );
        })}
      </div>
      {selected.length === 0 && (
        <p className="text-xs text-destructive">Select at least one format.</p>
      )}
    </div>
  );
}
