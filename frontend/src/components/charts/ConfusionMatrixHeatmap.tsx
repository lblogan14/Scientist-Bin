import { Fragment } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// Note: "Actual" label is placed to the left of the row headers, rotated vertically

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
          <div className="flex gap-1">
            {/* "Actual" rotated label + spacer to match row-header width */}
            <div className="flex shrink-0 items-center justify-center" style={{ width: "1.5rem" }}>
              <span
                className="text-muted-foreground text-xs font-medium"
                style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}
              >
                Actual
              </span>
            </div>

            {/* Main grid: row-header col + data cols */}
            <div
              className="grid gap-1"
              style={{
                gridTemplateColumns: `auto repeat(${labels.length}, minmax(3rem, 1fr))`,
              }}
            >
              {/* Row 0: corner cell + "Predicted" spanning all data columns */}
              <div />
              <div
                className="text-muted-foreground mb-1 text-center text-xs font-medium"
                style={{ gridColumn: `span ${labels.length}` }}
              >
                Predicted
              </div>

              {/* Row 1: corner + column label headers */}
              <div />
              {labels.map((label) => (
                <div
                  key={`col-${label}`}
                  className="text-muted-foreground truncate text-center text-xs font-medium"
                  title={label}
                >
                  {label}
                </div>
              ))}

              {/* Data rows */}
              {matrix.map((row, rowIdx) => (
                <Fragment key={`row-${rowIdx}`}>
                  <div
                    className="text-muted-foreground flex items-center justify-end pr-2 text-xs font-medium"
                    title={labels[rowIdx]}
                  >
                    <span className="max-w-20 truncate">{labels[rowIdx]}</span>
                  </div>
                  {row.map((value, colIdx) => (
                    <div
                      key={`${rowIdx}-${colIdx}`}
                      className={`flex min-h-10 items-center justify-center rounded-md text-sm font-medium ${getCellColor(value, maxVal)}`}
                      title={`True: ${labels[rowIdx]}, Predicted: ${labels[colIdx]}, Count: ${value}`}
                    >
                      {value}
                    </div>
                  ))}
                </Fragment>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
