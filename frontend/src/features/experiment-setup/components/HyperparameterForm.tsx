import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { isExperimentResult } from "@/types/api";
import type { ExecutionPlan, ExperimentRecord } from "@/types/api";
import { useExperiment } from "../hooks/use-experiment";

interface HyperparameterFormProps {
  experimentId: string | null;
}

export function HyperparameterForm({ experimentId }: HyperparameterFormProps) {
  const { data: experiment } = useExperiment(experimentId);

  if (!experimentId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Hyperparameters</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            Select an experiment to view hyperparameters.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (
    !experiment ||
    experiment.status !== "completed" ||
    !experiment.result ||
    !isExperimentResult(experiment.result)
  ) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Hyperparameters</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            Hyperparameters will appear once training completes.
          </p>
        </CardContent>
      </Card>
    );
  }

  const result = experiment.result;
  const plan = experiment.execution_plan as ExecutionPlan | null;
  const tuningStrategy = plan?.hyperparameter_tuning_approach;
  const bestHyperparams = result.best_hyperparameters;
  const history: ExperimentRecord[] = result.experiment_history ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Hyperparameters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Tuning strategy */}
        {tuningStrategy && (
          <div>
            <p className="text-muted-foreground mb-1 text-xs font-medium uppercase tracking-wide">
              Tuning Strategy
            </p>
            <p className="text-sm">{tuningStrategy}</p>
          </div>
        )}

        {/* Best hyperparameters */}
        {bestHyperparams && Object.keys(bestHyperparams).length > 0 && (
          <div>
            <p className="text-muted-foreground mb-1.5 text-xs font-medium uppercase tracking-wide">
              Best Hyperparameters
            </p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(bestHyperparams).map(([key, value]) => (
                <Badge key={key} variant="secondary">
                  {key}: {String(value)}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Per-algorithm hyperparameters */}
        {history.length > 0 && (
          <div className="space-y-3">
            <p className="text-muted-foreground text-xs font-medium uppercase tracking-wide">
              Per Algorithm
            </p>
            {history.map((record) => (
              <div key={`${record.algorithm}-${record.iteration}`}>
                <p className="mb-1 text-sm font-medium">{record.algorithm}</p>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(record.hyperparameters).length > 0 ? (
                    Object.entries(record.hyperparameters).map(
                      ([key, value]) => (
                        <Badge key={key} variant="outline">
                          {key}: {String(value)}
                        </Badge>
                      ),
                    )
                  ) : (
                    <span className="text-muted-foreground text-xs">
                      Default parameters
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
