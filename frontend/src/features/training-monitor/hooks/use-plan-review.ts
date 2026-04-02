import { useCallback, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { submitPlanReview, extractErrorMessage } from "@/lib/api-client";

export function usePlanReview(experimentId: string) {
  const queryClient = useQueryClient();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const clearError = useCallback(() => setErrorMessage(null), []);

  const mutation = useMutation({
    mutationFn: (feedback: string) =>
      submitPlanReview(experimentId, { feedback }),
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({
        queryKey: ["experiments", experimentId],
      });
      queryClient.invalidateQueries({
        queryKey: ["experiments"],
      });
    },
    onError: async (error) => {
      setErrorMessage(await extractErrorMessage(error));
    },
  });

  return { ...mutation, errorMessage, clearError };
}
