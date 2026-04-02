import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MetricPieChart } from "@/components/charts/MetricPieChart";
import { HorizontalBarChart } from "@/components/charts/HorizontalBarChart";
import type { DataProfile } from "@/types/api";

interface DataProfileCardProps {
  profile: DataProfile | null;
}

export function DataProfileCard({ profile }: DataProfileCardProps) {
  if (!profile) return null;

  const [rows, cols] = profile.shape;

  const classDistData = profile.class_distribution
    ? Object.entries(profile.class_distribution).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const columnTypeData = [
    { name: "Numeric", value: profile.numeric_columns.length },
    { name: "Categorical", value: profile.categorical_columns.length },
  ].filter((d) => d.value > 0);

  const missingData = Object.entries(profile.missing_counts)
    .filter(([, count]) => count > 0)
    .map(([name, value]) => ({ name, value }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Data Profile (EDA)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
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
            <p className="text-lg font-bold">
              {profile.numeric_columns.length}
            </p>
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

        {/* Charts row */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Class distribution pie chart */}
          {classDistData.length > 0 && (
            <MetricPieChart
              title="Class Distribution"
              data={classDistData}
              height={250}
            />
          )}

          {/* Column type donut */}
          {columnTypeData.length > 1 && (
            <MetricPieChart
              title="Column Types"
              data={columnTypeData}
              height={250}
            />
          )}
        </div>

        {/* Missing values chart */}
        {missingData.length > 0 && (
          <HorizontalBarChart
            title="Missing Values"
            data={missingData}
            color="var(--chart-5)"
            height={Math.max(150, missingData.length * 40)}
          />
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
