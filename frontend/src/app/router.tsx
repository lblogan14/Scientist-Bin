import { lazy } from "react";
import { createBrowserRouter } from "react-router";
import { Layout } from "./Layout";

const DashboardPage = lazy(
  () => import("@/features/dashboard/components/DashboardPage"),
);
const ExperimentSetupPage = lazy(
  () => import("@/features/experiment-setup/components/ExperimentSetupPage"),
);
const TrainingMonitorPage = lazy(
  () => import("@/features/training-monitor/components/TrainingMonitorPage"),
);
const ResultsPage = lazy(
  () => import("@/features/results/components/ResultsPage"),
);
const ModelSelectionPage = lazy(
  () => import("@/features/model-selection/components/ModelSelectionPage"),
);

export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "experiments", element: <ExperimentSetupPage /> },
      { path: "monitor", element: <TrainingMonitorPage /> },
      { path: "results", element: <ResultsPage /> },
      { path: "results/:id", element: <ResultsPage /> },
      { path: "models", element: <ModelSelectionPage /> },
    ],
  },
]);
