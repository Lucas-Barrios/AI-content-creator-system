import type { LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description: string;
  icon?: LucideIcon;
  badge?: string;
}

export function PageHeader({ eyebrow, title, description, icon: Icon, badge }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div>
        <div className="mb-2 flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4 text-primary" />}
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">{eyebrow}</p>
        </div>
        <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">{title}</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      {badge && <Badge variant="outline">{badge}</Badge>}
    </div>
  );
}
