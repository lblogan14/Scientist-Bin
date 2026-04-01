import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { submitTrainRequest } from "../api";

export function useSubmitTrain() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: submitTrainRequest,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["experiments"] });
      navigate(`/monitor?id=${data.id}`);
    },
  });
}
