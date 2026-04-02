import { useCallback, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { submitTrainRequest, extractErrorMessage } from "@/lib/api-client";

export function useSubmitTrain() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const clearError = useCallback(() => setErrorMessage(null), []);

  const mutation = useMutation({
    mutationFn: submitTrainRequest,
    onSuccess: (data) => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["experiments"] });
      navigate(`/monitor?id=${data.id}`);
    },
    onError: async (error) => {
      setErrorMessage(await extractErrorMessage(error));
    },
  });

  return { ...mutation, errorMessage, clearError };
}
