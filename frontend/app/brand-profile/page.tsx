"use client";

import { Palette, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/workspace/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { getBrandProfile, saveBrandProfile } from "@/lib/api-client";
import { useWorkspace } from "@/lib/hooks/use-workspace";

export default function BrandProfilePage() {
  const { workspace } = useWorkspace();
  const [profile, setProfile] = useState({
    name: "Default brand profile",
    positioning: "",
    voice: "",
    audience: "",
    approvedTerms: "",
    bannedTerms: "",
    complianceNotes: ""
  });
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    getBrandProfile(workspace.clientId, workspace.projectId)
      .then(({ profile: savedProfile }) => {
        if (!savedProfile) return;
        setProfile({
          name: savedProfile.name,
          positioning: savedProfile.positioning ?? "",
          voice: savedProfile.voice ?? "",
          audience: savedProfile.audience_summary ?? "",
          approvedTerms: savedProfile.approved_terms?.join(", ") ?? "",
          bannedTerms: savedProfile.banned_terms?.join(", ") ?? "",
          complianceNotes: savedProfile.compliance_notes ?? ""
        });
      })
      .catch(() => undefined);
  }, [workspace.clientId, workspace.projectId]);

  const save = async () => {
    setStatus("Saving...");
    try {
      await saveBrandProfile({
        organizationId: workspace.organizationId,
        clientId: workspace.clientId,
        projectId: workspace.projectId,
        name: profile.name,
        positioning: profile.positioning,
        voice: profile.voice,
        toneGuidelines: profile.voice,
        audienceSummary: profile.audience,
        approvedTerms: profile.approvedTerms.split(",").map((item) => item.trim()).filter(Boolean),
        bannedTerms: profile.bannedTerms.split(",").map((item) => item.trim()).filter(Boolean),
        complianceNotes: profile.complianceNotes,
        brandValues: []
      });
      setStatus("Saved to Supabase through the Python API.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not save brand profile.");
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-6">
        <PageHeader
          eyebrow="Brand Profile"
          title="Define brand memory for consistent content"
          description="Capture the rules the AI should use when generating future content. The Supabase schema is ready for persistence; this editor keeps a local draft until the brand-profile API is connected."
          icon={Palette}
          badge="Brand memory"
        />
        <Card>
          <CardHeader>
            <CardTitle>Brand profile draft</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-2 lg:col-span-2">
              <Label>Profile name</Label>
              <Input value={profile.name} onChange={(event) => setProfile({ ...profile, name: event.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Positioning</Label>
              <Textarea value={profile.positioning} onChange={(event) => setProfile({ ...profile, positioning: event.target.value })} placeholder="What does this brand stand for?" />
            </div>
            <div className="space-y-2">
              <Label>Voice</Label>
              <Textarea value={profile.voice} onChange={(event) => setProfile({ ...profile, voice: event.target.value })} placeholder="Describe the preferred tone and writing style." />
            </div>
            <div className="space-y-2">
              <Label>Audience summary</Label>
              <Textarea value={profile.audience} onChange={(event) => setProfile({ ...profile, audience: event.target.value })} placeholder="Who are we speaking to?" />
            </div>
            <div className="space-y-2">
              <Label>Compliance notes</Label>
              <Textarea value={profile.complianceNotes} onChange={(event) => setProfile({ ...profile, complianceNotes: event.target.value })} placeholder="Claims, legal, or sector-specific rules." />
            </div>
            <div className="space-y-2">
              <Label>Approved terms</Label>
              <Input value={profile.approvedTerms} onChange={(event) => setProfile({ ...profile, approvedTerms: event.target.value })} placeholder="Comma-separated preferred terms" />
            </div>
            <div className="space-y-2">
              <Label>Banned terms</Label>
              <Input value={profile.bannedTerms} onChange={(event) => setProfile({ ...profile, bannedTerms: event.target.value })} placeholder="Comma-separated avoided terms" />
            </div>
            <div className="lg:col-span-2 flex justify-end">
              <Button onClick={save}>
                <Save className="h-4 w-4" />
                Save brand profile
              </Button>
            </div>
            {status && <p className="text-sm text-muted-foreground lg:col-span-2">{status}</p>}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
