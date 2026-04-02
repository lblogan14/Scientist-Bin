import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ConsoleOutputProps {
  logs: string[];
}

export function ConsoleOutput({ logs }: ConsoleOutputProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Console Output
          {logs.length > 0 && (
            <span className="text-muted-foreground ml-2 font-normal">
              ({logs.length} lines)
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64">
          <pre className="bg-muted rounded-md p-4 font-mono text-xs">
            {logs.length === 0
              ? "Waiting for output..."
              : logs.map((line, i) => (
                  <div
                    key={i}
                    className={
                      line.toLowerCase().includes("error")
                        ? "text-destructive"
                        : line.startsWith("METRIC:")
                          ? "text-primary"
                          : ""
                    }
                  >
                    {line}
                  </div>
                ))}
            <div ref={bottomRef} />
          </pre>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
