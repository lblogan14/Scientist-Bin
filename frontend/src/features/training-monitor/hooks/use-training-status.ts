import { HTTPError } from "ky";
import { useQuery } from "@tanstack/react-query";
import { getExperiment } from "../api";

export function useTrainingStatus(id: string | null) {
  return useQuery({
    queryKey: ["experiments", id],
    queryFn: () => getExperiment(id!),
    enabled: !!id,
    retry: (failureCount, error) => {
      // Don't retry on 404 — the experiment is genuinely missing
      if (error instanceof HTTPError && error.response.status === 404) {
        return false;
      }
      // Be resilient to transient failures (timeout, network) during training
      return failureCount < 3;
    },
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10_000),
    // Reduced frequency — SSE is now the primary real-time channel.
    // Polling serves as a fallback to sync phase/status changes.
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 10_000 : false;
    },
  });
}
