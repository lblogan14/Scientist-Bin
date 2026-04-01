import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Experiment } from "@/types/api";

interface ModelActionsProps {
  model: Experiment;
}

export function ModelActions({ model }: ModelActionsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Actions</CardTitle>
      </CardHeader>
      <CardContent className="flex gap-2">
        <Button asChild variant="outline" size="sm">
          <Link to={`/results?id=${model.id}`}>View Code</Link>
        </Button>
        <Button asChild variant="outline" size="sm">
          <Link to={`/?objective=${encodeURIComponent(model.objective)}`}>
            Re-run
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
