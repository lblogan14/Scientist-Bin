import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricLineChart } from "@/components/charts/MetricLineChart";
import type { MetricPoint } from "@/types/api";

interface MetricsStreamProps {
  metrics: Map<string, MetricPoint[]>;
}

export function MetricsStream({ metrics }: MetricsStreamProps) {
  const metricNames = useMemo(() => Array.from(metrics.keys()), [metrics]);

  if (metricNames.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Live Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2">
          {metricNames.map((name) => {
            const points = metrics.get(name) ?? [];
            const chartData = points.map((p, idx) => ({
              step: p.step ?? idx,
              value: p.value,
            }));

            return (
              <MetricLineChart
                key={name}
                title={name}
                data={chartData}
                xKey="step"
                yKey="value"
              />
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
