import type { TabContext } from "../tab-registry";
import { ConfusionMatrixTab } from "./ConfusionMatrixTab";

export function ConfusionMatrixTabWrapper({
  chartData,
  experimentHistory,
}: TabContext) {
  return (
    <ConfusionMatrixTab
      matrices={chartData?.confusion_matrices}
      history={experimentHistory}
    />
  );
}
