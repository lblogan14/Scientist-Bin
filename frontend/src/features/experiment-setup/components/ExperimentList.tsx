import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { Eye, Activity } from "lucide-react";
import { listExperiments } from "../api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";
import { ExperimentFilterBar } from "./ExperimentFilterBar";

interface ExperimentListProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function statusBadgeVariant(
  status: string,
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "running":
      return "default";
    case "completed":
      return "secondary";
    case "failed":
      return "destructive";
    default:
      return "outline";
  }
}

export function ExperimentList({ selectedId, onSelect }: ExperimentListProps) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [frameworkFilter, setFrameworkFilter] = useState("all");

  const { data: experiments, isLoading } = useQuery({
    queryKey: ["experiments"],
    queryFn: () => listExperiments(),
    select: (data) => data.experiments,
  });

  // Client-side filtering (API also supports server-side)
  const filtered = useMemo(() => {
    if (!experiments) return [];
    return experiments.filter((exp) => {
      if (statusFilter !== "all" && exp.status !== statusFilter) return false;
      if (frameworkFilter !== "all" && exp.framework !== frameworkFilter)
        return false;
      if (
        search &&
        !exp.objective.toLowerCase().includes(search.toLowerCase()) &&
        !exp.id.toLowerCase().includes(search.toLowerCase())
      )
        return false;
      return true;
    });
  }, [experiments, search, statusFilter, frameworkFilter]);

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <ExperimentFilterBar
        search={search}
        onSearchChange={setSearch}
        status={statusFilter}
        onStatusChange={setStatusFilter}
        framework={frameworkFilter}
        onFrameworkChange={setFrameworkFilter}
      />

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Objective</TableHead>
            <TableHead>Framework</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Phase</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="w-20" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {filtered.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={6}
                className="text-muted-foreground text-center"
              >
                No experiments found.
              </TableCell>
            </TableRow>
          ) : (
            filtered.map((exp) => (
              <TableRow
                key={exp.id}
                className={`cursor-pointer ${selectedId === exp.id ? "bg-muted" : ""}`}
                onClick={() => onSelect(exp.id)}
              >
                <TableCell className="max-w-xs truncate">
                  {exp.objective}
                </TableCell>
                <TableCell>{exp.framework ?? "Auto"}</TableCell>
                <TableCell>
                  <Badge variant={statusBadgeVariant(exp.status)}>
                    {exp.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  {exp.phase && (
                    <Badge variant="outline" className="text-xs">
                      {exp.phase}
                    </Badge>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground text-xs">
                  {new Date(exp.created_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  {(exp.status === "running" || exp.status === "pending") && (
                    <Button variant="ghost" size="icon" asChild>
                      <Link to={`/monitor?id=${exp.id}`} title="Monitor">
                        <Activity className="size-4" />
                      </Link>
                    </Button>
                  )}
                  {exp.status === "completed" && (
                    <Button variant="ghost" size="icon" asChild>
                      <Link to={`/results?id=${exp.id}`} title="Results">
                        <Eye className="size-4" />
                      </Link>
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {experiments && (
        <p className="text-muted-foreground text-xs">
          Showing {filtered.length} of {experiments.length} experiments
        </p>
      )}
    </div>
  );
}
