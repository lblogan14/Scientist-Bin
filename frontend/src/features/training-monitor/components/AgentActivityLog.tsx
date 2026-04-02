import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AgentActivity } from "@/types/api";

interface AgentActivityLogProps {
  activities: AgentActivity[];
}

function getActionVariant(
  action: string,
): "default" | "secondary" | "destructive" | "outline" {
  const lower = action.toLowerCase();
  if (lower.includes("error") || lower.includes("failed")) return "destructive";
  if (lower.includes("complete") || lower.includes("done")) return "default";
  if (lower.includes("phase")) return "secondary";
  return "outline";
}

export function AgentActivityLog({ activities }: AgentActivityLogProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Agent Activity
          {activities.length > 0 && (
            <span className="text-muted-foreground ml-2 font-normal">
              ({activities.length})
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64">
          {activities.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No agent activity recorded yet.
            </p>
          ) : (
            <div className="space-y-2">
              {activities.map((act, i) => (
                <div key={i} className="border-border border-l-2 pl-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={getActionVariant(act.action)}
                      className="text-xs"
                    >
                      {act.action}
                    </Badge>
                    <span className="text-muted-foreground text-xs">
                      {new Date(act.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {act.details && (
                    <p className="text-muted-foreground mt-0.5">
                      {act.details}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
