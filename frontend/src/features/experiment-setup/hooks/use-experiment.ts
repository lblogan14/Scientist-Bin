import { useQuery } from "@tanstack/react-query";
import { getExperiment } from "../api";

export function useExperiment(id: string | null) {
  return useQuery({
    queryKey: ["experiments", id],
    queryFn: () => getExperiment(id!),
    enabled: !!id,
  });
}
