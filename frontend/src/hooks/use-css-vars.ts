import { useEffect, useState } from "react";
import { useAppStore } from "@/stores/app-store";

/** Read one or more CSS custom properties from :root as resolved color strings. */
export function useCssVars(names: string[]): string[] {
  const theme = useAppStore((s) => s.theme);

  const [values, setValues] = useState<string[]>(() =>
    names.map((n) =>
      getComputedStyle(document.documentElement).getPropertyValue(n).trim(),
    ),
  );

  useEffect(() => {
    // After theme class is applied, re-read the resolved values
    setValues(
      names.map((n) =>
        getComputedStyle(document.documentElement).getPropertyValue(n).trim(),
      ),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme]);

  return values;
}
