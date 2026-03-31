import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface EvaluationReportProps {
  evaluation: Record<string, unknown> | null;
}

export function EvaluationReport({ evaluation }: EvaluationReportProps) {
  if (!evaluation) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Evaluation Report</CardTitle>
      </CardHeader>
      <CardContent>
        <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs">
          {JSON.stringify(evaluation, null, 2)}
        </pre>
      </CardContent>
    </Card>
  );
}
