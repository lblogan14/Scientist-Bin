import { useQuery } from "@tanstack/react-query";
import { listExperiments } from "../api";

export function useExperiments() {
  return useQuery({
    queryKey: ["experiments"],
    queryFn: listExperiments,
  });
}
