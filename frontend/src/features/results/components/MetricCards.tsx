import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MetricCardsProps {
  metrics: Record<string, unknown> | null;
}

export function MetricCards({ metrics }: MetricCardsProps) {
  if (!metrics || Object.keys(metrics).length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Object.entries(metrics).map(([key, value]) => (
        <Card key={key}>
          <CardHeader className="pb-2">
            <CardTitle className="text-muted-foreground text-xs font-medium uppercase">
              {key}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {typeof value === "number" ? value.toFixed(4) : String(value)}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
