import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { ChartContainer } from "@/components/charts/ChartContainer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TabContext } from "../tab-registry";
import type { LearningCurvePoint } from "@/types/api";

export function LearningCurveTab({ chartData, experimentHistory }: TabContext) {
  const data: LearningCurvePoint[] =
    chartData?.learning_curve ??
    experimentHistory.findLast((r) => r.learning_curve?.length)
      ?.learning_curve ??
    [];

  if (data.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No learning curve data available.
      </p>
    );
  }

  // Detect overfitting/underfitting from the gap
  const lastPoint = data[data.length - 1];
  const gap = lastPoint
    ? Math.abs(lastPoint.train_score - lastPoint.val_score)
    : 0;
  const diagnosis =
    gap > 0.1
      ? "High variance (overfitting) detected — the model performs significantly better on training data."
      : gap > 0.05
        ? "Moderate variance — there is a noticeable gap between training and validation scores."
        : "Good fit — training and validation scores converge.";

  return (
    <div className="space-y-4">
      {/* Diagnosis card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Learning Curve Diagnosis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{diagnosis}</p>
          {lastPoint && (
            <p className="text-muted-foreground mt-1 text-xs">
              Final train score: {lastPoint.train_score.toFixed(4)} | Final
              validation score: {lastPoint.val_score.toFixed(4)} | Gap:{" "}
              {gap.toFixed(4)}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Learning curve chart */}
      <ChartContainer
        title="Learning Curve (Score vs Training Set Size)"
        height={350}
      >
        <LineChart
          data={data}
          margin={{ top: 10, right: 30, bottom: 20, left: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="train_size"
            label={{
              value: "Training Set Size",
              position: "insideBottom",
              offset: -10,
            }}
          />
          <YAxis
            domain={[0, 1]}
            label={{ value: "Score", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            content={({ payload }) => {
              if (!payload?.[0]) return null;
              const p = payload[0].payload as LearningCurvePoint;
              return (
                <div className="bg-background border rounded p-2 text-xs shadow">
                  <p>Train size: {p.train_size}</p>
                  <p>Train score: {p.train_score.toFixed(4)}</p>
                  <p>Val score: {p.val_score.toFixed(4)}</p>
                </div>
              );
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="train_score"
            name="Training Score"
            stroke="var(--chart-1)"
            strokeWidth={2}
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="val_score"
            name="Validation Score"
            stroke="var(--chart-2)"
            strokeWidth={2}
            dot={{ r: 4 }}
          />
        </LineChart>
      </ChartContainer>
    </div>
  );
}
