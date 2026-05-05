import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <Card className="border-dashed bg-white/70">
      <CardContent className="flex min-h-64 flex-col items-center justify-center p-8 text-center">
        <Icon className="mb-3 h-9 w-9 text-muted-foreground/55" />
        <p className="font-semibold">{title}</p>
        <p className="mt-1 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>
        {action && <div className="mt-4">{action}</div>}
      </CardContent>
    </Card>
  );
}
