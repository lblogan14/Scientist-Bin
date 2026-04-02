import { useMutation, useQueryClient } from "@tanstack/react-query";
import { submitPlanReview } from "@/lib/api-client";

export function usePlanReview(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (feedback: string) =>
      submitPlanReview(experimentId, { feedback }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["experiments", experimentId],
      });
      queryClient.invalidateQueries({
        queryKey: ["experiments"],
      });
    },
  });
}
