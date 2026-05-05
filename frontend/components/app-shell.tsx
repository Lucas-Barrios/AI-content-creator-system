import Image from "next/image";
import { FileText, History, MessageSquare, Megaphone } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { label: "Generator", icon: FileText, href: "/", active: false },
  { label: "Campaigns", icon: Megaphone, href: "/campaigns", active: false },
  { label: "Chat", icon: MessageSquare, href: "#chat", active: false },
  { label: "History", icon: History, href: "#history", active: false }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(232,78,15,0.08),transparent_28rem),linear-gradient(180deg,#fffdfb_0%,#f7f3ef_100%)]">
      <div className="grid min-h-screen lg:grid-cols-[280px_1fr]">
        <aside className="hidden border-r bg-neutral-950 text-white lg:block">
          <div className="flex h-full flex-col">
            <div className="flex items-center gap-3 px-5 py-5">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-white">
                <Image src="/srh_logo.png" width={38} height={38} alt="SRH logo" priority />
              </div>
              <div>
                <div className="font-semibold leading-tight">AI Content Creator</div>
                <div className="text-xs text-white/55">SRH demo workspace</div>
              </div>
            </div>
            <Separator className="bg-white/10" />
            <nav className="space-y-1 px-3 py-4">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  className={
                    item.active
                      ? "flex items-center gap-3 rounded-md bg-white px-3 py-2 text-sm font-semibold text-neutral-950 transition-colors"
                      : "flex items-center gap-3 rounded-md px-3 py-2 text-sm text-white/68 transition-colors hover:bg-white/10 hover:text-white"
                  }
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </a>
              ))}
            </nav>
            <div className="mt-auto p-4">
              <div className="rounded-lg border border-white/10 bg-white/[0.04] p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase text-white/45">Backend</span>
                  <Badge variant="secondary" className="border-white/10 bg-white/10 text-white">
                    API proxy
                  </Badge>
                </div>
                <p className="text-xs leading-5 text-white/60">
                  Next.js routes proxy requests to the Python backend via <code>PYTHON_API_BASE_URL</code>.
                </p>
              </div>
            </div>
          </div>
        </aside>
        <main className="min-w-0">
          <header className="sticky top-0 z-20 border-b bg-background/85 px-4 py-3 backdrop-blur md:px-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-primary">SRH University</p>
                <h1 className="text-xl font-semibold tracking-tight md:text-2xl">AI Content Operations</h1>
              </div>
              <div className="hidden items-center gap-2 md:flex">
                <Badge variant="success">Production UI</Badge>
                <Badge variant="outline">Next.js</Badge>
              </div>
            </div>
          </header>
          <div className="p-4 md:p-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
