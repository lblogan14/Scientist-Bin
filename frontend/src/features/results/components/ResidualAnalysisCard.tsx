import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ResidualStats } from "@/types/api";

interface ResidualAnalysisCardProps {
  residuals: Record<string, ResidualStats>;
}

export function ResidualAnalysisCard({ residuals }: ResidualAnalysisCardProps) {
  const algorithms = Object.keys(residuals);

  if (algorithms.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Residual Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Algorithm</TableHead>
              <TableHead className="text-right">Mean Residual</TableHead>
              <TableHead className="text-right">Std Residual</TableHead>
              <TableHead className="text-right">Max |Residual|</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {algorithms.map((algo) => {
              const stats = residuals[algo];
              if (!stats) return null;
              return (
                <TableRow key={algo}>
                  <TableCell className="font-medium">{algo}</TableCell>
                  <TableCell className="text-right font-mono">
                    {stats.mean_residual.toFixed(4)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {stats.std_residual.toFixed(4)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {stats.max_abs_residual.toFixed(4)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
