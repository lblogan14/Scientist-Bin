import type { TabContext } from "../tab-registry";
import { OverviewTab } from "./OverviewTab";

export function OverviewTabAdapter({ result }: TabContext) {
  if (!result) {
    return <p className="text-muted-foreground text-sm">No results available.</p>;
  }
  return <OverviewTab result={result} />;
}
