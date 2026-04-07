import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TabContext } from "../tab-registry";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EstimatorComparisonEntry } from "@/types/api";

const COLORS = [
  "hsl(var(--primary))",
  "hsl(var(--destructive))",
  "hsl(210, 70%, 50%)",
  "hsl(150, 60%, 45%)",
  "hsl(45, 80%, 50%)",
  "hsl(280, 60%, 55%)",
  "hsl(15, 70%, 50%)",
  "hsl(180, 50%, 45%)",
];

export function EstimatorComparisonTab({
  chartData,
  experimentHistory,
}: TabContext) {
  // Collect estimator comparison from chart data or experiment history
  let comparison: EstimatorComparisonEntry[] = [];

  if (chartData?.estimator_comparison?.length) {
    comparison = chartData.estimator_comparison;
  } else {
    for (const record of experimentHistory) {
      if (record.estimator_comparison?.length) {
        comparison = record.estimator_comparison;
        break;
      }
    }
  }

  // Filter out entries with null/undefined best_loss, then sort ascending
  const valid = comparison.filter((e) => e.best_loss != null);

  if (!valid.length) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-center">
            No estimator comparison data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  const sorted = [...valid].sort((a, b) => a.best_loss - b.best_loss);
  const bestEstimator = sorted[0]?.estimator;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Estimator Comparison (Best Loss)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={sorted} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis
                dataKey="estimator"
                type="category"
                width={100}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const first = payload[0];
                  if (!first) return null;
                  const data = first.payload as EstimatorComparisonEntry;
                  return (
                    <div className="bg-background border-border rounded-md border p-2 text-xs shadow-sm">
                      <p className="font-medium">{data.estimator}</p>
                      <p>Best Loss: {data.best_loss?.toFixed(4) ?? "N/A"}</p>
                      {data.best_config && (
                        <p className="mt-1 max-w-[200px] truncate">
                          Config: {JSON.stringify(data.best_config)}
                        </p>
                      )}
                    </div>
                  );
                }}
              />
              <Bar dataKey="best_loss" name="Best Loss" radius={[0, 4, 4, 0]}>
                {sorted.map((entry, index) => (
                  <Cell
                    key={entry.estimator}
                    fill={COLORS[index % COLORS.length]}
                    opacity={entry.estimator === bestEstimator ? 1 : 0.7}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Best Configuration per Estimator</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {sorted.map((entry) => (
              <div
                key={entry.estimator}
                className={`rounded-md border p-3 ${
                  entry.estimator === bestEstimator
                    ? "border-primary bg-primary/5"
                    : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    {entry.estimator}
                    {entry.estimator === bestEstimator && (
                      <span className="text-primary ml-2 text-xs">
                        Best
                      </span>
                    )}
                  </span>
                  <span className="text-muted-foreground text-sm">
                    Loss: {entry.best_loss?.toFixed(4) ?? "N/A"}
                  </span>
                </div>
                {entry.best_config &&
                  Object.keys(entry.best_config).length > 0 && (
                    <pre className="text-muted-foreground mt-1 overflow-x-auto text-xs">
                      {JSON.stringify(entry.best_config, null, 2)}
                    </pre>
                  )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
