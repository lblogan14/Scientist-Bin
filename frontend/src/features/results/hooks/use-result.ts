import { useQuery } from "@tanstack/react-query";
import { getExperiment } from "../api";

export function useResult(id: string | null) {
  return useQuery({
    queryKey: ["experiments", id],
    queryFn: () => getExperiment(id!),
    enabled: !!id,
    select: (data) => ({
      experiment: data,
      result: data.result,
    }),
  });
}
