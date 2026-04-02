import { ActiveExperimentBanner } from "./ActiveExperimentBanner";
import { DashboardStats } from "./DashboardStats";
import { ObjectiveForm } from "./ObjectiveForm";
import { RecentExperiments } from "./RecentExperiments";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>
      <ActiveExperimentBanner />
      <DashboardStats />
      <div className="grid gap-6 lg:grid-cols-2">
        <ObjectiveForm />
        <RecentExperiments />
      </div>
    </div>
  );
}
