import { useQuery } from "@tanstack/react-query";
import { listExperiments } from "../api";

export function useModels() {
  return useQuery({
    queryKey: ["experiments"],
    queryFn: listExperiments,
    select: (data) => data.filter((exp) => exp.status === "completed"),
  });
}
