import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCssVars } from "@/hooks/use-css-vars";

interface BoxPlotData {
  name: string;
  scores: number[];
  mean: number;
}

interface BoxPlotChartProps {
  data: BoxPlotData[];
  title?: string;
}

function computeStats(scores: number[]) {
  const sorted = [...scores].sort((a, b) => a - b);
  const n = sorted.length;
  return {
    min: sorted[0] ?? 0,
    q1: sorted[Math.floor(n * 0.25)] ?? 0,
    median: sorted[Math.floor(n * 0.5)] ?? 0,
    q3: sorted[Math.floor(n * 0.75)] ?? 0,
    max: sorted[n - 1] ?? 0,
    mean: scores.reduce((a, b) => a + b, 0) / (n || 1),
  };
}

export function BoxPlotChart({
  data,
  title = "CV Fold Distribution",
}: BoxPlotChartProps) {
  const chartVars = useCssVars([
    "--chart-1",
    "--chart-2",
    "--chart-3",
    "--chart-4",
    "--chart-5",
  ]);

  if (!data?.length) return null;

  // One row per fold, one column per algorithm
  const maxFolds = Math.max(...data.map((d) => d.scores.length), 0);
  const foldRows = Array.from({ length: maxFolds }, (_, foldIdx) => {
    const row: Record<string, number | string> = { fold: `Fold ${foldIdx + 1}` };
    for (const d of data) {
      row[d.name] = d.scores[foldIdx] ?? 0;
    }
    return row;
  });

  const stats = data.map((d) => ({ name: d.name, ...computeStats(d.scores) }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <ResponsiveContainer width="100%" height={Math.max(220, maxFolds * 40 + 60)}>
          <BarChart data={foldRows} margin={{ left: 10, right: 20, top: 10 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="fold" tick={{ fontSize: 11 }} />
            <YAxis
              tick={{ fontSize: 11 }}
              domain={["auto", "auto"]}
              tickFormatter={(v: number) => v.toFixed(3)}
            />
            <Tooltip
              formatter={(value: number, name: string) => [
                value.toFixed(4),
                name,
              ]}
            />
            <Legend />
            {data.map((d, i) => (
              <Bar
                key={d.name}
                dataKey={d.name}
                fill={chartVars[i % chartVars.length] ?? chartVars[0]}
                fillOpacity={0.8}
                radius={[3, 3, 0, 0]}
                barSize={Math.max(8, 40 / data.length)}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>

        {/* Stats summary table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b">
                <th className="text-muted-foreground px-2 py-1 text-left font-medium">Algorithm</th>
                <th className="text-muted-foreground px-2 py-1 text-right font-medium">Min</th>
                <th className="text-muted-foreground px-2 py-1 text-right font-medium">Q1</th>
                <th className="text-muted-foreground px-2 py-1 text-right font-medium">Median</th>
                <th className="text-muted-foreground px-2 py-1 text-right font-medium">Mean</th>
                <th className="text-muted-foreground px-2 py-1 text-right font-medium">Q3</th>
                <th className="text-muted-foreground px-2 py-1 text-right font-medium">Max</th>
              </tr>
            </thead>
            <tbody>
              {stats.map((s, i) => (
                <tr key={s.name} className="border-b last:border-0">
                  <td
                    className="px-2 py-1 font-medium"
                    style={{ color: chartVars[i % chartVars.length] }}
                  >
                    {s.name}
                  </td>
                  <td className="px-2 py-1 text-right font-mono">{s.min.toFixed(4)}</td>
                  <td className="px-2 py-1 text-right font-mono">{s.q1.toFixed(4)}</td>
                  <td className="px-2 py-1 text-right font-mono">{s.median.toFixed(4)}</td>
                  <td className="px-2 py-1 text-right font-mono">{s.mean.toFixed(4)}</td>
                  <td className="px-2 py-1 text-right font-mono">{s.q3.toFixed(4)}</td>
                  <td className="px-2 py-1 text-right font-mono">{s.max.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
