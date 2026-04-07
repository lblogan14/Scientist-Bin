import { Award, Target, TrendingUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { ParetoFrontierChart } from "@/components/charts/ParetoFrontierChart";
import type { ExperimentResult } from "@/types/api";
import { pickPrimaryMetric } from "@/lib/metric-utils";
import { MetricCards } from "./MetricCards";

interface OverviewTabProps {
  result: ExperimentResult;
}

export function OverviewTab({ result }: OverviewTabProps) {
  const sections = result.report_sections;
  const bestModel = result.best_model;
  const bestParams = result.best_hyperparameters;
  const reasoning = result.selection_reasoning;

  // Extract best experiment's metrics from history
  const bestExperiment = result.experiment_history?.find(
    (e) => e.algorithm === bestModel,
  );
  const bestMetrics = bestExperiment?.metrics ?? null;

  // Build Pareto data from experiment history
  const paretoData = result.experiment_history
    ?.filter((r) => r.training_time_seconds > 0)
    .map((r) => {
      const primaryMetric = pickPrimaryMetric(r.metrics, result.problem_type).value;
      return {
        name: r.algorithm,
        performance: primaryMetric,
        time: r.training_time_seconds,
        isPareto: r.algorithm === bestModel,
      };
    }) ?? [];

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      {sections?.executive_summary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <TrendingUp className="size-4" />
              Executive Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <MarkdownRenderer content={sections.executive_summary} />
          </CardContent>
        </Card>
      )}

      {/* Best Model Highlight */}
      {bestModel && (
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Award className="text-primary size-4" />
              Best Model
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold">{bestModel}</span>
              {result.problem_type && (
                <Badge variant="secondary">{result.problem_type}</Badge>
              )}
            </div>
            {bestParams && Object.keys(bestParams).length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(bestParams).map(([key, val]) => (
                  <Badge key={key} variant="outline" className="max-w-48 text-xs">
                    <span className="truncate">{key}: {String(val)}</span>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Key Metrics */}
      {bestMetrics && <MetricCards metrics={bestMetrics} />}

      {/* Performance vs Training Time */}
      {paretoData.length > 1 && <ParetoFrontierChart data={paretoData} />}

      {/* Selection Reasoning */}
      {reasoning && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Target className="size-4" />
              Why This Model?
            </CardTitle>
          </CardHeader>
          <CardContent>
            <MarkdownRenderer content={reasoning} />
          </CardContent>
        </Card>
      )}

      {/* Conclusions */}
      {sections?.conclusions && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Conclusions</CardTitle>
          </CardHeader>
          <CardContent>
            <MarkdownRenderer content={sections.conclusions} />
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {sections?.recommendations && sections.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-1 pl-4 text-sm">
              {sections.recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
