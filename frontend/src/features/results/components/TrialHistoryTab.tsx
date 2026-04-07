import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TabContext } from "../tab-registry";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrialHistoryPoint } from "@/types/api";

export function TrialHistoryTab({ chartData, experimentHistory }: TabContext) {
  // Collect trial history from chart data or experiment history
  let trialHistory: TrialHistoryPoint[] = [];

  if (chartData?.trial_history?.length) {
    trialHistory = chartData.trial_history;
  } else {
    for (const record of experimentHistory) {
      if (record.trial_history?.length) {
        trialHistory = record.trial_history;
        break;
      }
    }
  }

  if (!trialHistory.length) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-center">
            No trial history available.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Build convergence data: best loss so far at each trial
  let bestLoss = Infinity;
  const convergenceData = trialHistory.map((trial) => {
    if (trial.loss < bestLoss) {
      bestLoss = trial.loss;
    }
    return {
      trial_id: trial.trial_id,
      loss: trial.loss,
      best_loss: bestLoss,
      estimator: trial.estimator,
      time: trial.time,
    };
  });

  // Count unique estimators
  const estimatorCounts = new Map<string, number>();
  for (const trial of trialHistory) {
    estimatorCounts.set(
      trial.estimator,
      (estimatorCounts.get(trial.estimator) ?? 0) + 1,
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Trial Convergence</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={convergenceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="trial_id"
                label={{
                  value: "Trial",
                  position: "insideBottom",
                  offset: -5,
                }}
              />
              <YAxis
                label={{
                  value: "Loss",
                  angle: -90,
                  position: "insideLeft",
                }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const first = payload[0];
                  if (!first) return null;
                  const data = first.payload as (typeof convergenceData)[0];
                  return (
                    <div className="bg-background border-border rounded-md border p-2 text-xs shadow-sm">
                      <p className="font-medium">Trial {data.trial_id}</p>
                      <p>Estimator: {data.estimator}</p>
                      <p>Loss: {data.loss.toFixed(4)}</p>
                      <p>Best so far: {data.best_loss.toFixed(4)}</p>
                      <p>Time: {data.time.toFixed(1)}s</p>
                    </div>
                  );
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="loss"
                stroke="hsl(var(--muted-foreground) / 0.4)"
                strokeWidth={1}
                dot={{ r: 2 }}
                name="Trial Loss"
              />
              <Line
                type="stepAfter"
                dataKey="best_loss"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={false}
                name="Best Loss"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Trial Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
            <div>
              <p className="text-muted-foreground">Total Trials</p>
              <p className="text-lg font-semibold">{trialHistory.length}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Best Loss</p>
              <p className="text-lg font-semibold">{bestLoss.toFixed(4)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Best Estimator</p>
              <p className="text-lg font-semibold">
                {trialHistory.find((t) => t.loss === bestLoss)?.estimator ??
                  "—"}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Estimators Tried</p>
              <p className="text-lg font-semibold">{estimatorCounts.size}</p>
            </div>
          </div>
          <div className="mt-4">
            <p className="text-muted-foreground mb-2 text-sm font-medium">
              Trials per Estimator
            </p>
            <div className="flex flex-wrap gap-2">
              {[...estimatorCounts.entries()]
                .sort((a, b) => b[1] - a[1])
                .map(([est, count]) => (
                  <span
                    key={est}
                    className="bg-muted rounded-md px-2 py-1 text-xs"
                  >
                    {est}: {count}
                  </span>
                ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
