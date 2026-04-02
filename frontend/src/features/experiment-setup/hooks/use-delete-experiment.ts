import { useCallback, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteExperiment, extractErrorMessage } from "@/lib/api-client";

export function useDeleteExperiment() {
  const queryClient = useQueryClient();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const clearError = useCallback(() => setErrorMessage(null), []);

  const mutation = useMutation({
    mutationFn: deleteExperiment,
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["experiments"] });
    },
    onError: async (error) => {
      setErrorMessage(await extractErrorMessage(error));
    },
  });

  return { ...mutation, errorMessage, clearError };
}
