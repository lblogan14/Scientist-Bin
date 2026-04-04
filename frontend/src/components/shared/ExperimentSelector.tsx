import { useQuery } from "@tanstack/react-query";
import { listExperiments } from "@/lib/api-client";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ExperimentStatus } from "@/types/api";

interface ExperimentSelectorProps {
  statusFilter?: string[];
  value: string | null;
  onChange: (id: string) => void;
  showAllOption?: boolean;
  className?: string;
}

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + "..." : text;
}

function statusLabel(status: ExperimentStatus): string {
  switch (status) {
    case "completed":
      return "done";
    case "running":
      return "live";
    case "pending":
      return "queued";
    case "failed":
      return "err";
    default:
      return status;
  }
}

export function ExperimentSelector({
  statusFilter,
  value,
  onChange,
  showAllOption = false,
  className,
}: ExperimentSelectorProps) {
  const { data } = useQuery({
    queryKey: ["experiments"],
    queryFn: () => listExperiments(),
  });

  const experiments = data?.experiments ?? [];
  const filtered = statusFilter
    ? experiments.filter((e) => statusFilter.includes(e.status))
    : experiments;

  if (filtered.length === 0) {
    return (
      <Select disabled>
        <SelectTrigger className={className}>
          <SelectValue placeholder="No experiments" />
        </SelectTrigger>
      </Select>
    );
  }

  return (
    <Select value={value ?? undefined} onValueChange={onChange}>
      <SelectTrigger className={className}>
        <SelectValue placeholder="Select experiment" />
      </SelectTrigger>
      <SelectContent>
        {showAllOption && <SelectItem value="all">All experiments</SelectItem>}
        {filtered.map((exp) => (
          <SelectItem key={exp.id} value={exp.id}>
            {truncate(exp.objective, 35)} [{statusLabel(exp.status)}]
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
