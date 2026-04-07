import type { TabContext } from "../tab-registry";
import { AlgorithmComparisonChart } from "./AlgorithmComparisonChart";
import { AlgorithmRadarChart } from "./AlgorithmRadarChart";
import { EvaluationReport } from "./EvaluationReport";
import { TrainingTimeChart } from "./TrainingTimeChart";

export function ExperimentsTab({ result, experimentHistory }: TabContext) {
  const evaluationResults = result?.evaluation_results as Record<
    string,
    unknown
  > | null;

  return (
    <div className="space-y-4">
      <EvaluationReport
        evaluation={evaluationResults}
        experimentHistory={experimentHistory}
      />
      <div className="grid gap-4 md:grid-cols-2">
        <AlgorithmComparisonChart history={experimentHistory} />
        <TrainingTimeChart history={experimentHistory} />
      </div>
      <AlgorithmRadarChart history={experimentHistory} />
    </div>
  );
}
