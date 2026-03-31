import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface AgentActivityLogProps {
  activities: { agent: string; action: string; timestamp: string }[];
}

export function AgentActivityLog({ activities }: AgentActivityLogProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Agent Activity</CardTitle>
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
                <div
                  key={i}
                  className="border-border border-l-2 pl-3 text-sm"
                >
                  <p className="font-medium">{act.agent}</p>
                  <p className="text-muted-foreground">{act.action}</p>
                  <p className="text-muted-foreground text-xs">
                    {new Date(act.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
