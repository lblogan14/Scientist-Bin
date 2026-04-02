import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CVResultEntry } from "@/types/api";

interface HyperparamHeatmapProps {
  data: CVResultEntry[];
  title?: string;
}

function getScoreColor(score: number, min: number, max: number): string {
  const range = max - min;
  if (range === 0) return "bg-primary/40";
  const ratio = (score - min) / range;
  if (ratio > 0.8) return "bg-success text-success-foreground";
  if (ratio > 0.6) return "bg-success/50";
  if (ratio > 0.4) return "bg-warning/40";
  if (ratio > 0.2) return "bg-warning/25";
  return "bg-destructive/30";
}

export function HyperparamHeatmap({
  data,
  title = "Hyperparameter Search Results",
}: HyperparamHeatmapProps) {
  if (data.length === 0) return null;

  const minScore = Math.min(...data.map((d) => d.mean_score));
  const maxScore = Math.max(...data.map((d) => d.mean_score));

  // Get all param keys
  const paramKeys = Array.from(
    new Set(data.flatMap((d) => Object.keys(d.params))),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-muted-foreground px-2 py-1.5 text-left text-xs font-medium">
                Rank
              </th>
              {paramKeys.map((key) => (
                <th
                  key={key}
                  className="text-muted-foreground px-2 py-1.5 text-left text-xs font-medium"
                >
                  {key}
                </th>
              ))}
              <th className="text-muted-foreground px-2 py-1.5 text-right text-xs font-medium">
                Mean Score
              </th>
              <th className="text-muted-foreground px-2 py-1.5 text-right text-xs font-medium">
                Std
              </th>
            </tr>
          </thead>
          <tbody>
            {data
              .sort((a, b) => a.rank - b.rank)
              .map((entry, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="px-2 py-1.5 font-medium">{entry.rank}</td>
                  {paramKeys.map((key) => (
                    <td key={key} className="px-2 py-1.5 font-mono text-xs">
                      {String(entry.params[key] ?? "—")}
                    </td>
                  ))}
                  <td className="px-2 py-1.5 text-right">
                    <span
                      className={`inline-block rounded px-2 py-0.5 font-mono text-xs ${getScoreColor(entry.mean_score, minScore, maxScore)}`}
                    >
                      {entry.mean_score.toFixed(4)}
                    </span>
                  </td>
                  <td className="px-2 py-1.5 text-right font-mono text-xs">
                    {entry.std_score.toFixed(4)}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
