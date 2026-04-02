import { Download } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { getArtifactDownloadUrl } from "@/lib/api-client";
import type { ExecutionPlan } from "@/types/api";

interface PlanTabProps {
  /** Structured execution plan */
  executionPlan?: ExecutionPlan | Record<string, unknown> | null;
  /** Markdown version of the plan */
  planMarkdown?: string | null;
  experimentId: string;
}

export function PlanTab({
  executionPlan,
  planMarkdown,
  experimentId,
}: PlanTabProps) {
  if (!executionPlan && !planMarkdown) {
    return (
      <p className="text-muted-foreground text-sm">
        No execution plan available for this experiment.
      </p>
    );
  }

  const plan = executionPlan as ExecutionPlan | null;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" asChild>
          <a href={getArtifactDownloadUrl(experimentId, "plan")} download>
            <Download className="mr-1.5 size-3.5" />
            Download Plan
          </a>
        </Button>
      </div>

      {/* Structured plan view */}
      {plan && (
        <div className="grid gap-4 md:grid-cols-2">
          {plan.approach_summary && (
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="text-sm font-medium">
                  Approach Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{plan.approach_summary}</p>
              </CardContent>
            </Card>
          )}

          {plan.algorithms_to_try?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">
                  Algorithms to Try
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="list-decimal space-y-1 pl-4 text-sm">
                  {plan.algorithms_to_try.map((algo, i) => (
                    <li key={i}>{algo}</li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          )}

          {plan.pipeline_preprocessing_steps?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">
                  Preprocessing Pipeline
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {plan.pipeline_preprocessing_steps.map((step, i) => (
                    <Badge key={i} variant="secondary">
                      {step}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {plan.feature_engineering_steps?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">
                  Feature Engineering
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {plan.feature_engineering_steps.map((step, i) => (
                    <Badge key={i} variant="outline">
                      {step}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {plan.evaluation_metrics?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">
                  Evaluation Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {plan.evaluation_metrics.map((metric, i) => (
                    <Badge key={i}>{metric}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Training Strategy
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {plan.cv_strategy && (
                <div>
                  <span className="text-muted-foreground">CV Strategy:</span>{" "}
                  {plan.cv_strategy}
                </div>
              )}
              {plan.hyperparameter_tuning_approach && (
                <div>
                  <span className="text-muted-foreground">HP Tuning:</span>{" "}
                  {plan.hyperparameter_tuning_approach}
                </div>
              )}
              {plan.success_criteria &&
                Object.keys(plan.success_criteria).length > 0 && (
                  <div>
                    <span className="text-muted-foreground">
                      Success Criteria:
                    </span>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {Object.entries(plan.success_criteria).map(
                        ([metric, threshold]) => (
                          <Badge key={metric} variant="outline">
                            {metric} &ge; {threshold}
                          </Badge>
                        ),
                      )}
                    </div>
                  </div>
                )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Markdown fallback / full plan text */}
      {planMarkdown && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Full Plan Document
            </CardTitle>
          </CardHeader>
          <CardContent>
            <MarkdownRenderer content={planMarkdown} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
