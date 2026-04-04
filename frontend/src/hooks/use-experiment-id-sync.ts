import { useCallback, useEffect } from "react";
import { useSearchParams } from "react-router";
import { useAppStore } from "@/stores/app-store";

export function useExperimentIdSync() {
  const [searchParams, setSearchParams] = useSearchParams();
  const storeId = useAppStore((s) => s.selectedExperimentId);
  const setStoreId = useAppStore((s) => s.setSelectedExperimentId);

  const urlId = searchParams.get("id");

  // URL wins: sync URL -> store
  useEffect(() => {
    if (urlId && urlId !== storeId) {
      setStoreId(urlId);
    }
  }, [urlId, storeId, setStoreId]);

  // Store wins on navigation: sync store -> URL (only if URL has no id)
  useEffect(() => {
    if (!urlId && storeId) {
      setSearchParams({ id: storeId }, { replace: true });
    }
  }, [urlId, storeId, setSearchParams]);

  const experimentId = urlId ?? storeId;

  const setExperimentId = useCallback(
    (id: string | null) => {
      setStoreId(id);
      if (id) {
        setSearchParams({ id }, { replace: true });
      } else {
        searchParams.delete("id");
        setSearchParams(searchParams, { replace: true });
      }
    },
    [setStoreId, setSearchParams, searchParams],
  );

  return { experimentId, setExperimentId };
}
