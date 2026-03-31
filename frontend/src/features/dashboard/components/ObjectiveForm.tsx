import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSubmitTrain } from "../hooks/use-submit-train";

const formSchema = z.object({
  objective: z.string().min(10, "Objective must be at least 10 characters"),
  data_description: z.string().optional(),
  data_file_path: z.string().optional(),
  framework_preference: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

export function ObjectiveForm() {
  const { mutate, isPending } = useSubmitTrain();
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { objective: "", data_description: "" },
  });

  const onSubmit = (values: FormValues) => {
    mutate({
      objective: values.objective,
      data_description: values.data_description,
      data_file_path: values.data_file_path || undefined,
      framework_preference: values.framework_preference as
        | "sklearn"
        | undefined,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Training Experiment</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="objective">Objective</Label>
            <Textarea
              id="objective"
              placeholder="Describe what you want to achieve, e.g. 'Classify iris species from petal measurements'"
              {...register("objective")}
            />
            {errors.objective && (
              <p className="text-destructive text-sm">
                {errors.objective.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="data_description">Data Description (optional)</Label>
            <Input
              id="data_description"
              placeholder="e.g. '4 features, 3 classes, 150 samples'"
              {...register("data_description")}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="data_file_path">Dataset File Path (optional)</Label>
            <Input
              id="data_file_path"
              placeholder="e.g. 'data/iris_data/Iris.csv'"
              {...register("data_file_path")}
            />
            <p className="text-muted-foreground text-xs">
              Path to a CSV file on the server. The agent will run EDA and train models on this data.
            </p>
          </div>

          <div className="space-y-2">
            <Label>Framework</Label>
            <Select
              onValueChange={(val) => setValue("framework_preference", val)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Auto-detect" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto-detect</SelectItem>
                <SelectItem value="sklearn">Scikit-learn</SelectItem>
                <SelectItem value="pytorch" disabled>
                  PyTorch (coming soon)
                </SelectItem>
                <SelectItem value="tensorflow" disabled>
                  TensorFlow (coming soon)
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" disabled={isPending} className="w-full">
            {isPending ? "Launching..." : "Launch Training"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
