import { useState } from "react";
import { ExperimentList } from "./ExperimentList";
import { ExperimentDetail } from "./ExperimentDetail";
import { HyperparameterForm } from "./HyperparameterForm";

export default function ExperimentSetupPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Experiments</h2>
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <ExperimentList selectedId={selectedId} onSelect={setSelectedId} />
        </div>
        <div className="space-y-4">
          {selectedId ? (
            <>
              <ExperimentDetail
                experimentId={selectedId}
                onDeleted={() => setSelectedId(null)}
              />
              <HyperparameterForm />
            </>
          ) : (
            <p className="text-muted-foreground text-sm">
              Select an experiment to view details.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
