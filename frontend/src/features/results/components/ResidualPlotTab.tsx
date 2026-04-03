import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { ChartContainer } from "@/components/charts/ChartContainer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { TabContext } from "../tab-registry";
import type { ActualVsPredictedPoint, ResidualStats } from "@/types/api";

export function ResidualPlotTab({ chartData, experimentHistory }: TabContext) {
  // Get actual vs predicted data to compute residuals
  const avpData: ActualVsPredictedPoint[] =
    chartData?.actual_vs_predicted ??
    experimentHistory.findLast((r) => r.actual_vs_predicted?.length)
      ?.actual_vs_predicted ??
    [];

  // Get residual stats
  const residualStatsMap = chartData?.residual_stats ?? {};
  const residualStats: ResidualStats | undefined =
    Object.values(residualStatsMap)[0] ??
    experimentHistory.findLast((r) => r.residual_stats)?.residual_stats;

  // Compute residual scatter data from actual vs predicted
  const residualData = avpData.map((d) => ({
    predicted: d.predicted,
    residual: d.actual - d.predicted,
  }));

  if (residualData.length === 0 && !residualStats) {
    return (
      <p className="text-muted-foreground text-sm">
        No residual data available.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {/* Residual statistics */}
      {residualStats && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Residual Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Statistic</TableHead>
                  <TableHead>Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell>Mean Residual</TableCell>
                  <TableCell>{residualStats.mean_residual.toFixed(4)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Std Residual</TableCell>
                  <TableCell>{residualStats.std_residual.toFixed(4)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Max Abs Residual</TableCell>
                  <TableCell>
                    {residualStats.max_abs_residual.toFixed(4)}
                  </TableCell>
                </TableRow>
                {residualStats.residual_percentiles && (
                  <>
                    <TableRow>
                      <TableCell>25th Percentile</TableCell>
                      <TableCell>
                        {Number(
                          residualStats.residual_percentiles["25"] ?? 0,
                        ).toFixed(4)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Median (50th)</TableCell>
                      <TableCell>
                        {Number(
                          residualStats.residual_percentiles["50"] ?? 0,
                        ).toFixed(4)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>75th Percentile</TableCell>
                      <TableCell>
                        {Number(
                          residualStats.residual_percentiles["75"] ?? 0,
                        ).toFixed(4)}
                      </TableCell>
                    </TableRow>
                  </>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Residual scatter plot */}
      {residualData.length > 0 && (
        <ChartContainer title="Residual Plot (Predicted vs Residual)" height={400}>
          <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="predicted"
              name="Predicted"
              label={{
                value: "Predicted Values",
                position: "insideBottom",
                offset: -10,
              }}
            />
            <YAxis
              type="number"
              dataKey="residual"
              name="Residual"
              label={{
                value: "Residual",
                angle: -90,
                position: "insideLeft",
              }}
            />
            <Tooltip
              content={({ payload }) => {
                if (!payload?.[0]) return null;
                const p = payload[0].payload as {
                  predicted: number;
                  residual: number;
                };
                return (
                  <div className="bg-background border rounded p-2 text-xs shadow">
                    <p>Predicted: {p.predicted.toFixed(4)}</p>
                    <p>Residual: {p.residual.toFixed(4)}</p>
                  </div>
                );
              }}
            />
            <ReferenceLine y={0} stroke="var(--chart-3)" strokeDasharray="5 5" />
            <Scatter
              data={residualData}
              fill="var(--chart-2)"
              opacity={0.6}
              r={3}
            />
          </ScatterChart>
        </ChartContainer>
      )}
    </div>
  );
}
