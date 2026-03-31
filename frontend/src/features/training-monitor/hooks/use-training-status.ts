import { useQuery } from "@tanstack/react-query";
import { getExperiment } from "../api";

export function useTrainingStatus(id: string | null) {
  return useQuery({
    queryKey: ["experiments", id],
    queryFn: () => getExperiment(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 3_000 : false;
    },
  });
}
