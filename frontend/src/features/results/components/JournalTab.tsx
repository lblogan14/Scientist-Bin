import type { TabContext } from "../tab-registry";
import { JournalViewer } from "./JournalViewer";

export function JournalTab({ experimentId }: TabContext) {
  return <JournalViewer experimentId={experimentId} />;
}
