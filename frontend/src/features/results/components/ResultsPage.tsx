import { useSearchParams } from "react-router";
import { BarChart3 } from "lucide-react";
import { EmptyState } from "@/components/feedback/EmptyState";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useResult } from "../hooks/use-result";
import { CodeDisplay } from "./CodeDisplay";
import { DataProfileCard } from "./DataProfileCard";
import { EvaluationReport } from "./EvaluationReport";
import { JournalViewer } from "./JournalViewer";
import { MetricCards } from "./MetricCards";

export default function ResultsPage() {
  const [searchParams] = useSearchParams();
  const experimentId = searchParams.get("id");

  const { data, isLoading } = useResult(experimentId);

  if (!experimentId) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No experiment selected"
        description="Select an experiment from the Experiments page to view results."
      />
    );
  }

  if (isLoading) return <LoadingSpinner message="Loading results..." />;
  if (!data) return null;

  const { result } = data;
  const experimentHistory = result?.experiment_history ?? [];
  const dataProfile = result?.data_profile ?? null;
  const bestMetrics =
    result?.evaluation_results as Record<string, unknown> | null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h2 className="text-2xl font-bold">Results</h2>
        {result?.problem_type && (
          <Badge variant="secondary">{result.problem_type}</Badge>
        )}
        {result?.iterations != null && result.iterations > 0 && (
          <Badge variant="outline">{result.iterations} iterations</Badge>
        )}
      </div>

      {/* Best model metrics at the top */}
      <MetricCards metrics={bestMetrics} />

      <Tabs defaultValue="experiments">
        <TabsList>
          <TabsTrigger value="experiments">Experiments</TabsTrigger>
          <TabsTrigger value="code">Code</TabsTrigger>
          {dataProfile && <TabsTrigger value="data">Data Profile</TabsTrigger>}
          <TabsTrigger value="journal">Journal</TabsTrigger>
        </TabsList>

        <TabsContent value="experiments" className="mt-4">
          <EvaluationReport
            evaluation={bestMetrics}
            experimentHistory={experimentHistory}
          />
        </TabsContent>

        <TabsContent value="code" className="mt-4">
          <CodeDisplay code={result?.generated_code ?? null} />
        </TabsContent>

        {dataProfile && (
          <TabsContent value="data" className="mt-4">
            <DataProfileCard profile={dataProfile} />
          </TabsContent>
        )}

        <TabsContent value="journal" className="mt-4">
          <JournalViewer experimentId={experimentId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
