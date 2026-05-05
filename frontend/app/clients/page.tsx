import { Building2, CheckCircle2, Circle } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/workspace/page-header";
import { WorkspaceIdPanel } from "@/components/workspace/workspace-id-panel";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const AUTH_STEPS: { done: boolean; label: string; detail: string }[] = [
  {
    done: true,
    label: "Supabase schema with RLS",
    detail: "organizations, clients, projects, organization_members, brand_profiles — all tables exist with row-level security policies."
  },
  {
    done: true,
    label: "Demo tenant seed",
    detail: "Migration 20260506030000 inserts the three demo UUIDs so FK constraints pass without a real auth user."
  },
  {
    done: true,
    label: "Service-role backend access",
    detail: "Python backend uses the service-role key; match_document_chunks is patched to allow service-role callers so RAG returns results."
  },
  {
    done: true,
    label: "Browser & server Supabase client factories",
    detail: "frontend/lib/supabase/client.ts and server.ts are ready. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY in .env.local."
  },
  {
    done: true,
    label: "Workspace ID store (localStorage)",
    detail: "useWorkspace hook persists org/client/project IDs in localStorage. All pages read from it so every API call is tenant-scoped."
  },
  {
    done: false,
    label: "Login / sign-up page",
    detail: "Create app/login/page.tsx using createBrowserSupabaseClient().auth.signInWithPassword() or signInWithOAuth(). Redirect to /dashboard on success."
  },
  {
    done: false,
    label: "Auth session middleware",
    detail: "Add middleware.ts at the project root using @supabase/ssr (createServerClient). Redirect unauthenticated requests to /login for all routes except /login itself."
  },
  {
    done: false,
    label: "organization_members row for your user",
    detail: "After signing up, insert a row into organization_members linking your auth.users UUID to the demo org with role = 'owner'. Then the RLS policies will let the browser client query Supabase directly."
  },
  {
    done: false,
    label: "Load clients & projects from Supabase",
    detail: "Replace the WorkspaceIdPanel manual inputs with a dropdown that calls supabase.from('clients').select() and supabase.from('projects').select() filtered by the authed user's org, then writes the chosen IDs into useWorkspace."
  }
];

export default function ClientsPage() {
  const done = AUTH_STEPS.filter((s) => s.done).length;
  const total = AUTH_STEPS.length;

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-6">
        <PageHeader
          eyebrow="Clients & Projects"
          title="Workspace context"
          description="The database schema, RLS policies, and backend service-role access are fully wired. User-facing auth (login page + session middleware) and a database-backed client/project picker are the remaining steps."
          icon={Building2}
          badge="Tenant scoped"
        />

        <WorkspaceIdPanel />

        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>Auth &amp; workspace wiring checklist</CardTitle>
              <CardDescription>Steps completed and still pending to replace manual ID entry with a full auth-gated client picker.</CardDescription>
            </div>
            <Badge variant={done === total ? "success" : "secondary"} className="shrink-0 text-xs">
              {done} / {total} done
            </Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            {AUTH_STEPS.map((step) => (
              <div key={step.label} className="flex gap-3 rounded-lg border bg-background p-3">
                {step.done
                  ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                  : <Circle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />}
                <div className="min-w-0">
                  <p className={`text-sm font-medium ${step.done ? "text-foreground" : "text-muted-foreground"}`}>
                    {step.label}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{step.detail}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
