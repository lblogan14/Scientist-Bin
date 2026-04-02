import { Link } from "react-router";
import { FlaskConical } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/feedback/EmptyState";
import { useExperiments } from "../hooks/use-experiments";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-500",
  running: "bg-blue-500",
  completed: "bg-green-500",
  failed: "bg-red-500",
};

export function RecentExperiments() {
  const { data: experiments, isLoading } = useExperiments();

  if (isLoading) return null;

  const recent = experiments?.slice(0, 5) ?? [];

  if (recent.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <EmptyState
            icon={FlaskConical}
            title="No experiments yet"
            description="Launch your first training experiment above."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Recent Experiments
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {recent.map((exp) => (
            <Link
              key={exp.id}
              to={
                exp.status === "completed"
                  ? `/results?id=${exp.id}`
                  : `/monitor?id=${exp.id}`
              }
              className="hover:bg-muted flex items-center gap-3 rounded-md p-2 transition"
            >
              <span
                className={`size-2 shrink-0 rounded-full ${statusColors[exp.status] ?? "bg-gray-500"}`}
              />
              <span className="flex-1 truncate text-sm">{exp.objective}</span>
              {exp.phase && exp.phase !== "done" && (
                <Badge variant="secondary" className="shrink-0 text-xs">
                  {exp.phase}
                </Badge>
              )}
              {exp.iteration_count > 0 && (
                <span className="text-muted-foreground shrink-0 text-xs">
                  {exp.iteration_count} iter
                </span>
              )}
              <Badge variant="outline" className="shrink-0 text-xs">
                {exp.status}
              </Badge>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
