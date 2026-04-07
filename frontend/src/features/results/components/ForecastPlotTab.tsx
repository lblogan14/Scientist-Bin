import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TabContext } from "../tab-registry";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ForecastDataPoint } from "@/types/api";

export function ForecastPlotTab({ chartData, experimentHistory }: TabContext) {
  // Collect forecast data from chart data or experiment history
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

  if (!forecastData.length) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-center">
            No forecast data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Format data for Recharts
  const chartPoints = forecastData.map((d) => ({
    timestamp: d.timestamp,
    actual: d.actual,
    predicted: d.predicted,
    lower: d.lower,
    upper: d.upper,
    // For the confidence band area
    confidence: d.lower != null && d.upper != null ? [d.lower, d.upper] : undefined,
  }));

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Forecast vs Actual</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={chartPoints}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 11 }}
                angle={-30}
                textAnchor="end"
                height={60}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              {chartPoints.some((p) => p.lower != null) && (
                <Area
                  type="monotone"
                  dataKey="confidence"
                  fill="hsl(var(--primary) / 0.1)"
                  stroke="none"
                  name="Confidence Interval"
                />
              )}
              <Line
                type="monotone"
                dataKey="actual"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={false}
                name="Actual"
              />
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="hsl(var(--destructive))"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name="Predicted"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Forecast Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
            <div>
              <p className="text-muted-foreground">Total Points</p>
              <p className="text-lg font-semibold">{forecastData.length}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Actual Points</p>
              <p className="text-lg font-semibold">
                {forecastData.filter((d) => d.actual != null).length}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Has Confidence</p>
              <p className="text-lg font-semibold">
                {forecastData.some((d) => d.lower != null) ? "Yes" : "No"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
