import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ConsoleOutputProps {
  logs: string[];
}

export function ConsoleOutput({ logs }: ConsoleOutputProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Console Output</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64">
          <pre className="bg-muted rounded-md p-4 font-mono text-xs">
            {logs.length === 0
              ? "Waiting for output..."
              : logs.join("\n")}
          </pre>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
