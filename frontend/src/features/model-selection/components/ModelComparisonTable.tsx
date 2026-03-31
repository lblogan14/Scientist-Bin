import { Link } from "react-router";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Experiment } from "@/types/api";

interface ModelComparisonTableProps {
  models: Experiment[];
}

export function ModelComparisonTable({ models }: ModelComparisonTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Objective</TableHead>
          <TableHead>Framework</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {models.map((model) => (
          <TableRow key={model.id}>
            <TableCell className="max-w-xs truncate">
              {model.objective}
            </TableCell>
            <TableCell>
              <Badge variant="outline">{model.framework ?? "Auto"}</Badge>
            </TableCell>
            <TableCell>
              <Badge>{model.status}</Badge>
            </TableCell>
            <TableCell className="text-muted-foreground text-xs">
              {new Date(model.created_at).toLocaleString()}
            </TableCell>
            <TableCell>
              <Link
                to={`/results?id=${model.id}`}
                className="text-primary text-sm hover:underline"
              >
                View Results
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
