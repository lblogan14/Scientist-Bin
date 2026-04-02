import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useSubmitTrain } from "../hooks/use-submit-train";

const formSchema = z.object({
  objective: z.string().min(10, "Objective must be at least 10 characters"),
  data_description: z.string().optional(),
  data_file_path: z.string().optional(),
  framework_preference: z.string().optional(),
  auto_approve_plan: z.boolean().optional(),
});

type FormValues = z.infer<typeof formSchema>;

export function ObjectiveForm() {
  const { mutate, isPending } = useSubmitTrain();
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      objective: "",
      data_description: "",
      auto_approve_plan: false,
    },
  });

  const autoApprove = watch("auto_approve_plan");

  const onSubmit = (values: FormValues) => {
    const fw = values.framework_preference;
    mutate({
      objective: values.objective,
      data_description: values.data_description,
      data_file_path: values.data_file_path || undefined,
      framework_preference: fw && fw !== "auto" ? (fw as "sklearn") : undefined,
      auto_approve_plan: values.auto_approve_plan || undefined,
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
            <Label htmlFor="data_description">
              Data Description (optional)
            </Label>
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
              placeholder="e.g. 'iris_data/Iris.csv'"
              {...register("data_file_path")}
            />
            <p className="text-muted-foreground text-xs">
              Path relative to <code className="text-xs">backend/data/</code>.
              The agent will run EDA and train models on this data.
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

          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="space-y-0.5">
              <Label htmlFor="auto_approve_plan">Auto-approve plan</Label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <p className="text-muted-foreground cursor-help text-xs">
                    Skip the plan review step
                  </p>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-64">
                  When enabled, the execution plan created by the Plan agent
                  will be automatically approved without waiting for your
                  review. Disable this to inspect and revise the plan before
                  training begins.
                </TooltipContent>
              </Tooltip>
            </div>
            <Switch
              id="auto_approve_plan"
              checked={autoApprove ?? false}
              onCheckedChange={(checked) =>
                setValue("auto_approve_plan", checked)
              }
            />
          </div>

          <Button type="submit" disabled={isPending} className="w-full">
            {isPending ? "Launching..." : "Launch Training"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
