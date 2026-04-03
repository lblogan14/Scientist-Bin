import type { TabContext } from "../tab-registry";
import { FeatureImportanceTab } from "./FeatureImportanceTab";

export function FeatureTabWrapper({
  chartData,
  experimentHistory,
}: TabContext) {
  return (
    <FeatureImportanceTab chartData={chartData} history={experimentHistory} />
  );
}
