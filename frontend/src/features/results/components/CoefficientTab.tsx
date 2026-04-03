import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from "recharts";
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
import type { CoefficientEntry } from "@/types/api";

export function CoefficientTab({ chartData, experimentHistory }: TabContext) {
  const coefficients: CoefficientEntry[] =
    chartData?.coefficients ??
    experimentHistory.findLast((r) => r.coefficients?.length)?.coefficients ??
    [];

  if (coefficients.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No coefficient data available. Coefficients are only available for
        linear models.
      </p>
    );
  }

  // Sort by absolute value descending
  const sorted = [...coefficients].sort(
    (a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient),
  );
  // Top 20 for the chart
  const chartCoeffs = sorted.slice(0, 20);

  return (
    <div className="space-y-4">
      {/* Horizontal bar chart */}
      <ChartContainer
        title="Feature Coefficients (Top 20 by Absolute Value)"
        height={Math.max(300, chartCoeffs.length * 28)}
      >
        <BarChart
          data={chartCoeffs}
          layout="vertical"
          margin={{ top: 10, right: 30, bottom: 10, left: 120 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis
            type="category"
            dataKey="feature"
            width={110}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            content={({ payload }) => {
              if (!payload?.[0]) return null;
              const p = payload[0].payload as CoefficientEntry;
              return (
                <div className="bg-background border rounded p-2 text-xs shadow">
                  <p className="font-medium">{p.feature}</p>
                  <p>Coefficient: {p.coefficient.toFixed(6)}</p>
                </div>
              );
            }}
          />
          <Bar dataKey="coefficient" maxBarSize={20}>
            {chartCoeffs.map((c, i) => (
              <Cell
                key={i}
                fill={c.coefficient >= 0 ? "var(--chart-2)" : "var(--chart-1)"}
              />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>

      {/* Full coefficient table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            All Feature Coefficients
          </CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rank</TableHead>
                <TableHead>Feature</TableHead>
                <TableHead>Coefficient</TableHead>
                <TableHead>|Coefficient|</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sorted.map((c, i) => (
                <TableRow key={c.feature}>
                  <TableCell>{i + 1}</TableCell>
                  <TableCell className="font-medium">{c.feature}</TableCell>
                  <TableCell
                    className={
                      c.coefficient >= 0 ? "text-green-600" : "text-red-600"
                    }
                  >
                    {c.coefficient.toFixed(6)}
                  </TableCell>
                  <TableCell>
                    {Math.abs(c.coefficient).toFixed(6)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
