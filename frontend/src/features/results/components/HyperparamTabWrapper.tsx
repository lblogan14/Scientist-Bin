import type { TabContext } from "../tab-registry";
import { HyperparameterTab } from "./HyperparameterTab";

export function HyperparamTabWrapper({
  result,
  chartData,
  experimentHistory,
}: TabContext) {
  return (
    <HyperparameterTab
      chartData={chartData}
      history={experimentHistory}
      result={result ?? undefined}
    />
  );
}
