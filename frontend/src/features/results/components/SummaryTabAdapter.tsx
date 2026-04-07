import type { TabContext } from "../tab-registry";
import { SummaryTab } from "./SummaryTab";

export function SummaryTabAdapter({ experiment, result, experimentId }: TabContext) {
  return (
    <SummaryTab
      summaryReport={experiment.summary_report ?? result?.summary_report ?? null}
      sections={result?.report_sections ?? null}
      experimentId={experimentId}
    />
  );
}
