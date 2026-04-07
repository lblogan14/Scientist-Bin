import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TabContext } from "../tab-registry";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function SeasonalProfileTab({ result }: TabContext) {
  const dataProfile = result?.data_profile;

  if (!dataProfile) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-center">
            No seasonal profile data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  const acfValues = dataProfile.autocorrelation_values;
  const stationarity = dataProfile.stationarity;
  const seasonalStrength = dataProfile.seasonal_strength;
  const trendDirection = dataProfile.trend_direction;
  const frequency = dataProfile.detected_frequency;
  const period = dataProfile.suggested_period;

  const hasAnyData =
    acfValues?.length || stationarity || seasonalStrength != null;

  if (!hasAnyData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-center">
            No time series profiling data available. This analysis requires
            statsmodels to be installed.
          </p>
        </CardContent>
      </Card>
    );
  }

  // ACF bar chart data
  const acfData =
    acfValues?.map((val, i) => ({
      lag: i,
      acf: val,
    })) ?? [];

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <Card>
        <CardHeader>
          <CardTitle>Time Series Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-5">
            <div>
              <p className="text-muted-foreground">Frequency</p>
              <p className="text-lg font-semibold">{frequency ?? "Unknown"}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Period</p>
              <p className="text-lg font-semibold">
                {period ?? "Unknown"}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Stationarity</p>
              <p className="text-lg font-semibold">
                {stationarity ? (
                  <span
                    className={
                      stationarity.is_stationary
                        ? "text-green-500"
                        : "text-amber-500"
                    }
                  >
                    {stationarity.is_stationary
                      ? "Stationary"
                      : "Non-stationary"}
                  </span>
                ) : (
                  "N/A"
                )}
              </p>
              {stationarity && (
                <p className="text-muted-foreground text-xs">
                  p={stationarity.p_value.toFixed(4)}
                </p>
              )}
            </div>
            <div>
              <p className="text-muted-foreground">Seasonal Strength</p>
              <p className="text-lg font-semibold">
                {seasonalStrength != null
                  ? `${(seasonalStrength * 100).toFixed(1)}%`
                  : "N/A"}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Trend</p>
              <p className="text-lg font-semibold capitalize">
                {trendDirection ?? "N/A"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ACF Chart */}
      {acfData.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Autocorrelation (ACF)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={acfData.slice(1)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="lag"
                  label={{
                    value: "Lag",
                    position: "insideBottom",
                    offset: -5,
                  }}
                />
                <YAxis
                  domain={[-1, 1]}
                  label={{
                    value: "ACF",
                    angle: -90,
                    position: "insideLeft",
                  }}
                />
                <Tooltip
                  formatter={(value: number) => [value.toFixed(4), "ACF"]}
                />
                <Bar
                  dataKey="acf"
                  fill="hsl(var(--primary))"
                  radius={[2, 2, 0, 0]}
                  name="ACF"
                />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-muted-foreground mt-2 text-center text-xs">
              High ACF at regular intervals indicates seasonality. Values above
              0.2 or below -0.2 are typically significant.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
