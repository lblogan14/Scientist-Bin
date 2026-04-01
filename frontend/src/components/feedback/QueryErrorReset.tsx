import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface QueryErrorResetProps {
  error: Error;
  onRetry: () => void;
}

export function QueryErrorReset({ error, onRetry }: QueryErrorResetProps) {
  return (
    <div className="flex flex-col items-center gap-4 py-12">
      <AlertCircle className="text-destructive size-8" />
      <p className="text-muted-foreground text-sm">{error.message}</p>
      <Button variant="outline" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}
