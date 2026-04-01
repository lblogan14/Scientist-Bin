import { useState } from "react";
import { AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface ErrorDisplayProps {
  error: string;
  traceback?: string;
}

export function ErrorDisplay({ error, traceback }: ErrorDisplayProps) {
  const [showTraceback, setShowTraceback] = useState(false);

  return (
    <Card className="border-destructive bg-destructive/5">
      <CardHeader>
        <CardTitle className="text-destructive flex items-center gap-2 text-sm font-medium">
          <AlertTriangle className="size-4" />
          Experiment Failed
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm">{error}</p>
        {traceback && (
          <div>
            <button
              type="button"
              onClick={() => setShowTraceback(!showTraceback)}
              className="text-muted-foreground hover:text-foreground flex items-center gap-1 text-xs"
            >
              {showTraceback ? (
                <ChevronDown className="size-3" />
              ) : (
                <ChevronRight className="size-3" />
              )}
              Traceback
            </button>
            {showTraceback && (
              <pre className="bg-muted mt-2 max-h-80 overflow-auto rounded p-3 text-xs">
                {traceback}
              </pre>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
