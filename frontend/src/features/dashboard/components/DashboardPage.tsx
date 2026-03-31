import { DashboardStats } from "./DashboardStats";
import { ObjectiveForm } from "./ObjectiveForm";
import { RecentExperiments } from "./RecentExperiments";

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>
      <DashboardStats />
      <ObjectiveForm />
      <RecentExperiments />
    </div>
  );
}
