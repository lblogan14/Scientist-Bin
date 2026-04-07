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
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
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
  deep_research: z.boolean().optional(),
  budget_max_iterations: z.coerce.number().int().min(1).max(100).optional(),
  budget_time_limit_hours: z.coerce.number().min(0.1).max(168).optional(),
});

type FormValues = z.infer<typeof formSchema>;

export function ObjectiveForm() {
  const { mutate, isPending, errorMessage, clearError } = useSubmitTrain();
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
      deep_research: false,
      budget_max_iterations: 10,
      budget_time_limit_hours: 4,
    },
  });

  const autoApprove = watch("auto_approve_plan");
  const deepResearch = watch("deep_research");

  const onSubmit = (values: FormValues) => {
    const fw = values.framework_preference;
    mutate({
      objective: values.objective,
      data_description: values.data_description,
      data_file_path: values.data_file_path || undefined,
      framework_preference: fw && fw !== "auto" ? (fw as "sklearn") : undefined,
      auto_approve_plan: values.auto_approve_plan || undefined,
      deep_research: values.deep_research || undefined,
      budget_max_iterations: values.deep_research
        ? values.budget_max_iterations
        : undefined,
      budget_time_limit_seconds: values.deep_research
        ? (values.budget_time_limit_hours ?? 4) * 3600
        : undefined,
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
              <p className="text-destructive text-sm" role="alert">
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

          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="space-y-0.5">
              <Label htmlFor="deep_research">Deep Research</Label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <p className="text-muted-foreground cursor-help text-xs">
                    Autonomous multi-experiment campaign
                  </p>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-64">
                  Runs an iterative research campaign that generates hypotheses,
                  executes experiments, extracts insights, and repeats until the
                  budget is exhausted. Requires a dataset file path.
                </TooltipContent>
              </Tooltip>
            </div>
            <Switch
              id="deep_research"
              checked={deepResearch ?? false}
              onCheckedChange={(checked) => {
                setValue("deep_research", checked);
                if (checked) {
                  setValue("auto_approve_plan", true);
                }
              }}
            />
          </div>

          {deepResearch && (
            <Accordion type="single" collapsible defaultValue="advanced">
              <AccordionItem value="advanced" className="border-none">
                <AccordionTrigger className="py-2 text-sm font-medium">
                  Advanced Campaign Settings
                </AccordionTrigger>
                <AccordionContent className="space-y-3 pt-1">
                  <div className="space-y-2">
                    <Label htmlFor="budget_max_iterations">
                      Max iterations
                    </Label>
                    <Input
                      id="budget_max_iterations"
                      type="number"
                      min={1}
                      max={100}
                      {...register("budget_max_iterations")}
                    />
                    <p className="text-muted-foreground text-xs">
                      Maximum number of experiments to run in the campaign.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="budget_time_limit_hours">
                      Time limit (hours)
                    </Label>
                    <Input
                      id="budget_time_limit_hours"
                      type="number"
                      min={0.1}
                      max={168}
                      step={0.5}
                      {...register("budget_time_limit_hours")}
                    />
                    <p className="text-muted-foreground text-xs">
                      Wall-clock time limit for the entire campaign.
                    </p>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}

          {errorMessage && (
            <div
              className="flex items-center justify-between rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
              role="alert"
            >
              <span>{errorMessage}</span>
              <button
                type="button"
                onClick={clearError}
                className="text-destructive/70 hover:text-destructive ml-2"
                aria-label="Dismiss error"
              >
                &times;
              </button>
            </div>
          )}

          <Button type="submit" disabled={isPending} className="w-full">
            {isPending
              ? deepResearch
                ? "Launching Campaign..."
                : "Launching..."
              : deepResearch
                ? "Launch Deep Research"
                : "Launch Training"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
