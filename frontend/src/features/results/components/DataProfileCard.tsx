import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { DataProfile } from "@/types/api";

interface DataProfileCardProps {
  profile: DataProfile | null;
}

export function DataProfileCard({ profile }: DataProfileCardProps) {
  if (!profile) return null;

  const [rows, cols] = profile.shape;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Data Profile (EDA)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Key stats */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-muted-foreground text-xs">Rows</p>
            <p className="text-lg font-bold">{rows.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Columns</p>
            <p className="text-lg font-bold">{cols}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Numeric</p>
            <p className="text-lg font-bold">{profile.numeric_columns.length}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Categorical</p>
            <p className="text-lg font-bold">
              {profile.categorical_columns.length}
            </p>
          </div>
        </div>

        {/* Target column */}
        {profile.target_column && (
          <div>
            <p className="text-muted-foreground text-xs">Target Column</p>
            <Badge variant="secondary">{profile.target_column}</Badge>
          </div>
        )}

        {/* Class distribution */}
        {profile.class_distribution && (
          <div>
            <p className="text-muted-foreground mb-1 text-xs">
              Class Distribution
            </p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(profile.class_distribution).map(
                ([cls, count]) => (
                  <Badge key={cls} variant="outline">
                    {cls}: {count}
                  </Badge>
                ),
              )}
            </div>
          </div>
        )}

        {/* Missing values */}
        {Object.keys(profile.missing_counts).length > 0 && (
          <div>
            <p className="text-muted-foreground mb-1 text-xs">Missing Values</p>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Column</TableHead>
                  <TableHead>Missing</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(profile.missing_counts).map(([col, count]) => (
                  <TableRow key={col}>
                    <TableCell className="font-mono text-xs">{col}</TableCell>
                    <TableCell>{count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Data quality issues */}
        {profile.data_quality_issues.length > 0 && (
          <div>
            <p className="text-muted-foreground mb-1 text-xs">
              Data Quality Issues
            </p>
            <ul className="list-inside list-disc text-sm">
              {profile.data_quality_issues.map((issue, i) => (
                <li key={i} className="text-yellow-600">
                  {issue}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
