import type { TabContext } from "../tab-registry";
import { DataProfileCard } from "./DataProfileCard";

export function DataTab({ result }: TabContext) {
  return <DataProfileCard profile={result?.data_profile ?? null} />;
}
