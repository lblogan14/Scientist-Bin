import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { getArtifactDownloadUrl } from "@/lib/api-client";

interface AnalysisTabProps {
  analysisReport: string | null;
  splitDataPaths?: Record<string, string> | null;
  experimentId: string;
}

export function AnalysisTab({
  analysisReport,
  splitDataPaths,
  experimentId,
}: AnalysisTabProps) {
  if (!analysisReport) {
    return (
      <p className="text-muted-foreground text-sm">
        No data analysis report available for this experiment.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" asChild>
          <a href={getArtifactDownloadUrl(experimentId, "analysis")} download>
            <Download className="mr-1.5 size-3.5" />
            Download Report
          </a>
        </Button>
      </div>

      {/* Split data paths */}
      {splitDataPaths && Object.keys(splitDataPaths).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Train / Validation / Test Split
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(splitDataPaths).map(([key, path]) => (
                <Badge key={key} variant="outline">
                  {key}: {String(path).split("/").pop()}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-6">
          <MarkdownRenderer content={analysisReport} />
        </CardContent>
      </Card>
    </div>
  );
}
