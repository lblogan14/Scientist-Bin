import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function HyperparameterForm() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Hyperparameters</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground text-sm">
          Hyperparameter configuration will be available in a future update.
          Currently, the agent automatically selects optimal parameters.
        </p>
      </CardContent>
    </Card>
  );
}
