import type { TabContext } from "../tab-registry";
import { AnalysisTab } from "./AnalysisTab";

export function AnalysisTabAdapter({ experiment, result, experimentId }: TabContext) {
  return (
    <AnalysisTab
      analysisReport={experiment.analysis_report ?? result?.analysis_report ?? null}
      splitDataPaths={experiment.split_data_paths}
      experimentId={experimentId}
    />
  );
}
