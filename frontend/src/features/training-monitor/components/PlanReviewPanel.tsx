import { useState } from "react";
import { CheckCircle2, MessageSquare, RotateCcw } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { usePlanReview } from "../hooks/use-plan-review";

interface PlanReviewPanelProps {
  experimentId: string;
  planMarkdown: string;
  revisionCount: number;
}

export function PlanReviewPanel({
  experimentId,
  planMarkdown,
  revisionCount,
}: PlanReviewPanelProps) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");
  const { mutate, isPending, errorMessage } = usePlanReview(experimentId);

  const handleApprove = () => {
    mutate("approve");
  };

  const handleRequestRevision = () => {
    if (!feedback.trim()) return;
    mutate(feedback.trim());
    setFeedback("");
    setShowFeedback(false);
  };

  return (
    <div className="space-y-4">
      <Alert className="border-amber-500/50 bg-amber-500/10">
        <MessageSquare className="size-4 text-amber-600" />
        <AlertTitle className="text-amber-700 dark:text-amber-400">
          Plan Review Required
        </AlertTitle>
        <AlertDescription className="text-amber-600 dark:text-amber-300">
          The Plan agent has created an execution plan. Review it below and
          approve or request changes before training begins.
          {revisionCount > 0 && (
            <Badge variant="outline" className="ml-2">
              Revision {revisionCount}
            </Badge>
          )}
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Execution Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-[500px] overflow-y-auto rounded-md border p-4">
            <MarkdownRenderer content={planMarkdown} />
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-3">
        {showFeedback && (
          <div className="space-y-2">
            <Textarea
              placeholder="Describe what changes you'd like to the plan..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={3}
            />
            <div className="flex gap-2">
              <Button
                onClick={handleRequestRevision}
                disabled={isPending || !feedback.trim()}
                variant="outline"
                size="sm"
              >
                <RotateCcw className="mr-1.5 size-3.5" />
                {isPending ? "Submitting..." : "Submit Feedback"}
              </Button>
              <Button
                onClick={() => setShowFeedback(false)}
                variant="ghost"
                size="sm"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {errorMessage && (
          <p className="text-destructive text-sm" role="alert">
            {errorMessage}
          </p>
        )}

        <div className="flex gap-3">
          <Button onClick={handleApprove} disabled={isPending}>
            <CheckCircle2 className="mr-1.5 size-4" />
            {isPending ? "Approving..." : "Approve Plan"}
          </Button>
          {!showFeedback && (
            <Button
              onClick={() => setShowFeedback(true)}
              variant="outline"
              disabled={isPending}
            >
              <RotateCcw className="mr-1.5 size-4" />
              Request Revision
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
