import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TabContext } from "../tab-registry";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ForecastDataPoint } from "@/types/api";

export function ForecastErrorTab({ chartData, experimentHistory }: TabContext) {
  let forecastData: ForecastDataPoint[] = [];

  if (chartData?.forecast_data?.length) {
    forecastData = chartData.forecast_data;
  } else {
    for (const record of experimentHistory) {
      if (record.forecast_data?.length) {
        forecastData = record.forecast_data;
        break;
      }
    }
  }

  // Filter to points with both actual and predicted
  const validPoints = forecastData.filter(
    (d) => d.actual != null && d.predicted != null,
  );

  if (!validPoints.length) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-center">
            No forecast error data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Compute errors
  const errors = validPoints.map((d) => ({
    timestamp: d.timestamp,
    error: d.actual! - d.predicted,
    absError: Math.abs(d.actual! - d.predicted),
    pctError:
      d.actual !== 0
        ? Math.abs((d.actual! - d.predicted) / d.actual!) * 100
        : 0,
  }));

  // Error statistics
  const absErrors = errors.map((e) => e.absError);
  const meanAbsError = absErrors.reduce((a, b) => a + b, 0) / absErrors.length;
  const maxAbsError = Math.max(...absErrors);
  const pctErrors = errors.map((e) => e.pctError);
  const meanPctError =
    pctErrors.reduce((a, b) => a + b, 0) / pctErrors.length;
  const rmse = Math.sqrt(
    errors.map((e) => e.error ** 2).reduce((a, b) => a + b, 0) /
      errors.length,
  );

  // Histogram bins for error distribution
  const minErr = Math.min(...errors.map((e) => e.error));
  const maxErr = Math.max(...errors.map((e) => e.error));
  const binCount = Math.min(20, Math.max(5, Math.floor(errors.length / 5)));
  const binWidth = (maxErr - minErr) / binCount || 1;
  const bins = Array.from({ length: binCount }, (_, i) => {
    const lo = minErr + i * binWidth;
    const hi = lo + binWidth;
    const count = errors.filter((e) => e.error >= lo && e.error < hi).length;
    return {
      range: `${lo.toFixed(1)}`,
      count,
    };
  });

  return (
    <div className="space-y-4">
      {/* Error metrics summary */}
      <Card>
        <CardHeader>
          <CardTitle>Forecast Error Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
            <div>
              <p className="text-muted-foreground">MAPE</p>
              <p className="text-lg font-semibold">
                {meanPctError.toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">RMSE</p>
              <p className="text-lg font-semibold">{rmse.toFixed(4)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">MAE</p>
              <p className="text-lg font-semibold">
                {meanAbsError.toFixed(4)}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Max Abs Error</p>
              <p className="text-lg font-semibold">
                {maxAbsError.toFixed(4)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error over time */}
      <Card>
        <CardHeader>
          <CardTitle>Error Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={errors}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 10 }}
                angle={-30}
                textAnchor="end"
                height={60}
              />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="error"
                stroke="hsl(var(--primary))"
                strokeWidth={1.5}
                dot={{ r: 2 }}
                name="Error (Actual - Predicted)"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Error distribution histogram */}
      <Card>
        <CardHeader>
          <CardTitle>Error Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={bins}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="range"
                tick={{ fontSize: 10 }}
                angle={-30}
                textAnchor="end"
                height={50}
              />
              <YAxis />
              <Tooltip />
              <Bar
                dataKey="count"
                fill="hsl(var(--primary))"
                radius={[4, 4, 0, 0]}
                name="Count"
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
