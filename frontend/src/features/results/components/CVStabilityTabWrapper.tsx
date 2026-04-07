import type { TabContext } from "../tab-registry";
import { CVStabilityTab } from "./CVStabilityTab";

export function CVStabilityTabWrapper({
  chartData,
  experimentHistory,
}: TabContext) {
  return <CVStabilityTab chartData={chartData} history={experimentHistory} />;
}
