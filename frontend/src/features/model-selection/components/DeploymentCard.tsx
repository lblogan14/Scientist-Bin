import { useState } from "react";
import { Rocket, Square, CheckCircle2, Loader2, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { deployModel, undeployModel } from "@/lib/api-client";
import type { DeploymentStatus } from "@/types/api";

interface DeploymentCardProps {
  experimentId: string;
  modelName: string;
}

const STATUS_CONFIG: Record<
  DeploymentStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline"; icon: typeof CheckCircle2 }
> = {
  not_deployed: { label: "Not Deployed", variant: "outline", icon: Square },
  deploying: { label: "Deploying...", variant: "secondary", icon: Loader2 },
  deployed: { label: "Deployed", variant: "default", icon: CheckCircle2 },
  failed: { label: "Failed", variant: "destructive", icon: AlertTriangle },
  stopped: { label: "Stopped", variant: "outline", icon: Square },
};

export function DeploymentCard({ experimentId, modelName }: DeploymentCardProps) {
  const [status, setStatus] = useState<DeploymentStatus>("not_deployed");
  const [endpointUrl, setEndpointUrl] = useState<string | null>(null);
  const [deployedAt, setDeployedAt] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleDeploy = async () => {
    setIsLoading(true);
    setStatus("deploying");
    setMessage(null);
    try {
      const result = await deployModel(experimentId);
      setStatus(result.status);
      setEndpointUrl(result.endpoint_url);
      setDeployedAt(result.deployed_at);
      setMessage("Model deployed successfully!");
    } catch {
      setStatus("failed");
      setMessage("Deployment failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUndeploy = async () => {
    setIsLoading(true);
    setMessage(null);
    try {
      await undeployModel(experimentId);
      setStatus("not_deployed");
      setEndpointUrl(null);
      setDeployedAt(null);
      setMessage("Model undeployed successfully.");
    } catch {
      setMessage("Failed to undeploy. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const config = STATUS_CONFIG[status];
  const StatusIcon = config.icon;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-sm font-medium">
          <div className="flex items-center gap-2">
            <Rocket className="size-4" />
            Deployment — {modelName}
          </div>
          <Badge variant={config.variant}>
            <StatusIcon
              className={`mr-1 size-3 ${status === "deploying" ? "animate-spin" : ""}`}
            />
            {config.label}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {endpointUrl && status === "deployed" && (
          <div className="space-y-1">
            <p className="text-muted-foreground text-xs">Endpoint URL</p>
            <code className="bg-muted rounded px-2 py-1 text-xs">
              {endpointUrl}
            </code>
          </div>
        )}

        {deployedAt && status === "deployed" && (
          <p className="text-muted-foreground text-xs">
            Deployed at: {new Date(deployedAt).toLocaleString()}
          </p>
        )}

        {message && (
          <p
            className={`text-sm ${
              message.includes("successfully")
                ? "text-green-600"
                : "text-red-600"
            }`}
          >
            {message}
          </p>
        )}

        <div className="flex gap-2">
          {status !== "deployed" ? (
            <Button
              size="sm"
              onClick={handleDeploy}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="mr-1 size-4 animate-spin" />
              ) : (
                <Rocket className="mr-1 size-4" />
              )}
              Deploy Model
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={handleUndeploy}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="mr-1 size-4 animate-spin" />
              ) : (
                <Square className="mr-1 size-4" />
              )}
              Undeploy
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
