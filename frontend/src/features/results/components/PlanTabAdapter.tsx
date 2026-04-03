import type { TabContext } from "../tab-registry";
import { PlanTab } from "./PlanTab";

export function PlanTabAdapter({ experiment, result, experimentId }: TabContext) {
  return (
    <PlanTab
      executionPlan={experiment.execution_plan ?? result?.plan ?? null}
      planMarkdown={result?.plan_markdown ?? null}
      experimentId={experimentId}
    />
  );
}
