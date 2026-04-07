import type { TabContext } from "../tab-registry";
import { CodeDisplay } from "./CodeDisplay";

export function CodeTab({ result }: TabContext) {
  return <CodeDisplay code={result?.generated_code ?? null} />;
}
