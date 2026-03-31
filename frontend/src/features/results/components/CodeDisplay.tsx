import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface CodeDisplayProps {
  code: string | null;
}

export function CodeDisplay({ code }: CodeDisplayProps) {
  if (!code) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-sm">
            No code generated yet.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Generated Code</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-96">
          <pre className="bg-muted overflow-x-auto rounded-md p-4 font-mono text-xs">
            <code>{code}</code>
          </pre>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
