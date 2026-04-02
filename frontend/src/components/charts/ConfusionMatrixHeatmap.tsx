import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ConfusionMatrixHeatmapProps {
  labels: string[];
  matrix: number[][];
  title?: string;
}

function getCellColor(value: number, max: number): string {
  if (max === 0) return "bg-muted";
  const ratio = value / max;
  if (ratio > 0.8) return "bg-primary/80 text-primary-foreground";
  if (ratio > 0.5) return "bg-primary/50 text-primary-foreground";
  if (ratio > 0.2) return "bg-primary/25";
  if (ratio > 0) return "bg-primary/10";
  return "bg-muted";
}

export function ConfusionMatrixHeatmap({
  labels,
  matrix,
  title = "Confusion Matrix",
}: ConfusionMatrixHeatmapProps) {
  const maxVal = Math.max(...matrix.flat(), 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          {/* Column headers label */}
          <div className="text-muted-foreground mb-1 text-center text-xs font-medium">
            Predicted
          </div>
          <div
            className="mx-auto grid w-fit gap-1"
            style={{
              gridTemplateColumns: `auto repeat(${labels.length}, minmax(3rem, 1fr))`,
            }}
          >
            {/* Top-left corner */}
            <div />
            {/* Column headers */}
            {labels.map((label) => (
              <div
                key={`col-${label}`}
                className="text-muted-foreground truncate text-center text-xs font-medium"
                title={label}
              >
                {label}
              </div>
            ))}

            {/* Rows */}
            {matrix.map((row, rowIdx) => (
              <>
                {/* Row header */}
                <div
                  key={`row-${labels[rowIdx]}`}
                  className="text-muted-foreground flex items-center justify-end pr-2 text-xs font-medium"
                  title={labels[rowIdx]}
                >
                  <span className="max-w-20 truncate">{labels[rowIdx]}</span>
                </div>
                {/* Cells */}
                {row.map((value, colIdx) => (
                  <div
                    key={`${rowIdx}-${colIdx}`}
                    className={`flex min-h-10 items-center justify-center rounded-md text-sm font-medium ${getCellColor(value, maxVal)}`}
                    title={`True: ${labels[rowIdx]}, Predicted: ${labels[colIdx]}, Count: ${value}`}
                  >
                    {value}
                  </div>
                ))}
              </>
            ))}
          </div>
          {/* Row headers label */}
          <div className="text-muted-foreground mt-1 text-center text-xs font-medium">
            Actual
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
