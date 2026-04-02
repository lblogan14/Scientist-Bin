import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getExperimentJournal } from "@/lib/api-client";
import type { JournalEntry } from "@/types/api";

interface JournalViewerProps {
  experimentId: string;
}

function getEventVariant(
  event: string,
): "default" | "secondary" | "destructive" | "outline" {
  if (event.includes("error") || event.includes("fail")) return "destructive";
  if (event.includes("complete") || event.includes("result")) return "default";
  if (event.includes("decision") || event.includes("reflection"))
    return "secondary";
  return "outline";
}

export function JournalViewer({ experimentId }: JournalViewerProps) {
  const { data: entries = [], isLoading } = useQuery<JournalEntry[]>({
    queryKey: ["journal", experimentId],
    queryFn: () => getExperimentJournal(experimentId),
    enabled: !!experimentId,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Experiment Journal
          {entries.length > 0 && (
            <span className="text-muted-foreground ml-2 font-normal">
              ({entries.length} entries)
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-80">
          {isLoading ? (
            <p className="text-muted-foreground text-sm">Loading journal...</p>
          ) : entries.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No journal entries yet.
            </p>
          ) : (
            <div className="space-y-3">
              {entries.map((entry, i) => (
                <div key={i} className="border-border border-l-2 pl-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={getEventVariant(entry.event)}
                      className="text-xs"
                    >
                      {entry.event}
                    </Badge>
                    {entry.phase && (
                      <span className="text-muted-foreground text-xs">
                        {entry.phase}
                      </span>
                    )}
                    {entry.iteration != null && (
                      <span className="text-muted-foreground text-xs">
                        iter {entry.iteration}
                      </span>
                    )}
                    <span className="text-muted-foreground ml-auto text-xs">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {entry.reasoning && (
                    <p className="text-muted-foreground mt-0.5">
                      {entry.reasoning}
                    </p>
                  )}
                  {entry.data &&
                    Object.keys(entry.data).length > 0 &&
                    "metrics" in entry.data &&
                    typeof entry.data.metrics === "object" &&
                    entry.data.metrics !== null && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {Object.entries(
                          entry.data.metrics as Record<string, number>,
                        ).map(([k, v]) => (
                          <Badge key={k} variant="outline" className="text-xs">
                            {k}: {typeof v === "number" ? v.toFixed(4) : v}
                          </Badge>
                        ))}
                      </div>
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
