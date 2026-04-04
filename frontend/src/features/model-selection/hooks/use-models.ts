import { useQuery } from "@tanstack/react-query";
import { listExperiments } from "../api";

export function useModels(experimentId?: string | null) {
  return useQuery({
    queryKey: ["experiments"],
    queryFn: () => listExperiments(),
    select: (data) => {
      const completed = data.experiments.filter(
        (exp) => exp.status === "completed",
      );
      if (experimentId && experimentId !== "all") {
        return completed.filter((exp) => exp.id === experimentId);
      }
      return completed;
    },
  });
}
