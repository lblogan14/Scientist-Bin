import { useQuery } from "@tanstack/react-query";
import { listExperiments } from "../api";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

interface ExperimentListProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function ExperimentList({ selectedId, onSelect }: ExperimentListProps) {
  const { data: experiments, isLoading } = useQuery({
    queryKey: ["experiments"],
    queryFn: () => listExperiments(),
    select: (data) => data.experiments,
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Objective</TableHead>
          <TableHead>Framework</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {experiments?.map((exp) => (
          <TableRow
            key={exp.id}
            className={`cursor-pointer ${selectedId === exp.id ? "bg-muted" : ""}`}
            onClick={() => onSelect(exp.id)}
          >
            <TableCell className="max-w-xs truncate">{exp.objective}</TableCell>
            <TableCell>{exp.framework ?? "Auto"}</TableCell>
            <TableCell>
              <Badge variant="outline">{exp.status}</Badge>
            </TableCell>
            <TableCell className="text-muted-foreground text-xs">
              {new Date(exp.created_at).toLocaleString()}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
