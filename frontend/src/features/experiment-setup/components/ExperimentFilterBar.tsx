import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ExperimentFilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  status: string;
  onStatusChange: (value: string) => void;
  framework: string;
  onFrameworkChange: (value: string) => void;
}

export function ExperimentFilterBar({
  search,
  onSearchChange,
  status,
  onStatusChange,
  framework,
  onFrameworkChange,
}: ExperimentFilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="relative min-w-48 flex-1">
        <Search className="text-muted-foreground absolute top-2.5 left-2.5 size-4" />
        <Input
          placeholder="Search experiments..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>
      <Select value={status} onValueChange={onStatusChange}>
        <SelectTrigger className="w-36">
          <SelectValue placeholder="All statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All statuses</SelectItem>
          <SelectItem value="pending">Pending</SelectItem>
          <SelectItem value="running">Running</SelectItem>
          <SelectItem value="completed">Completed</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
        </SelectContent>
      </Select>
      <Select value={framework} onValueChange={onFrameworkChange}>
        <SelectTrigger className="w-36">
          <SelectValue placeholder="All frameworks" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All frameworks</SelectItem>
          <SelectItem value="sklearn">Scikit-learn</SelectItem>
          <SelectItem value="pytorch">PyTorch</SelectItem>
          <SelectItem value="tensorflow">TensorFlow</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
