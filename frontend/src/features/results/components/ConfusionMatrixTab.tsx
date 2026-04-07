import { useState, useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ConfusionMatrixHeatmap } from "@/components/charts/ConfusionMatrixHeatmap";
import type { ConfusionMatrix, ExperimentRecord } from "@/types/api";

interface ConfusionMatrixTabProps {
  /** chart_data.confusion_matrices from summary agent */
  matrices?: Record<string, ConfusionMatrix>;
  /** Fallback: per-record confusion matrices */
  history?: ExperimentRecord[];
}

function getMatrices(
  props: ConfusionMatrixTabProps,
): Record<string, ConfusionMatrix> {
  if (props.matrices && Object.keys(props.matrices).length > 0) {
    return props.matrices;
  }
  // Fallback: extract from experiment history
  const out: Record<string, ConfusionMatrix> = {};
  for (const rec of props.history ?? []) {
    if (rec.confusion_matrix) {
      out[rec.algorithm] = rec.confusion_matrix;
    }
  }
  return out;
}

export function ConfusionMatrixTab(props: ConfusionMatrixTabProps) {
  const matrices = getMatrices(props);
  const algorithms = Object.keys(matrices);
  const [selected, setSelected] = useState(algorithms[0] ?? "");

  const algorithmsKey = algorithms.join(",");
  useEffect(() => {
    setSelected((prev) => {
      if (algorithms.includes(prev)) return prev;
      return algorithms[0] ?? "";
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [algorithmsKey]);

  if (algorithms.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No confusion matrix data available for this experiment.
      </p>
    );
  }

  const cm = matrices[selected];

  return (
    <div className="space-y-4">
      {algorithms.length > 1 && (
        <Select value={selected} onValueChange={setSelected}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select algorithm" />
          </SelectTrigger>
          <SelectContent>
            {algorithms.map((algo) => (
              <SelectItem key={algo} value={algo}>
                {algo}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {cm && (
        <ConfusionMatrixHeatmap
          labels={cm.labels}
          matrix={cm.matrix}
          title={`Confusion Matrix — ${selected}`}
        />
      )}
    </div>
  );
}
