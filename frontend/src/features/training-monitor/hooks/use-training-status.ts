import { useQuery } from "@tanstack/react-query";
import { getExperiment } from "../api";

export function useTrainingStatus(id: string | null) {
  return useQuery({
    queryKey: ["experiments", id],
    queryFn: () => getExperiment(id!),
    enabled: !!id,
    // Reduced frequency — SSE is now the primary real-time channel.
    // Polling serves as a fallback to sync phase/status changes.
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 10_000 : false;
    },
  });
}
