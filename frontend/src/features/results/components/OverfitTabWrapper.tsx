import type { TabContext } from "../tab-registry";
import { OverfitAnalysisTab } from "./OverfitAnalysisTab";

export function OverfitTabWrapper({ experimentHistory }: TabContext) {
  return <OverfitAnalysisTab history={experimentHistory} />;
}
