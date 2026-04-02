import { Link } from "react-router";
import { MessageSquare } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useExperiments } from "../hooks/use-experiments";

export function ActiveExperimentBanner() {
  const { data: experiments } = useExperiments();

  const reviewPending = experiments?.find((e) => e.phase === "plan_review");

  if (!reviewPending) return null;

  return (
    <Alert className="border-amber-500/50 bg-amber-500/10">
      <MessageSquare className="size-4 text-amber-600" />
      <AlertTitle className="text-amber-700 dark:text-amber-400">
        Plan Review Needed
      </AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span className="text-amber-600 dark:text-amber-300">
          &ldquo;{reviewPending.objective}&rdquo; is waiting for your plan
          approval.
        </span>
        <Button variant="outline" size="sm" asChild className="ml-4 shrink-0">
          <Link to={`/monitor?id=${reviewPending.id}`}>Review Plan</Link>
        </Button>
      </AlertDescription>
    </Alert>
  );
}
