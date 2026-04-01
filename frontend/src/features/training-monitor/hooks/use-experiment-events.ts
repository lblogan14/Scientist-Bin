import { useCallback, useEffect, useRef, useState } from "react";
import { createExperimentEventSource } from "@/lib/api-client";
import type {
  AgentActivity,
  MetricPoint,
  ProgressEvent,
} from "@/types/api";

interface ExperimentEvents {
  /** Timestamped agent activity entries */
  activities: AgentActivity[];
  /** Console log lines (stdout/stderr from execution) */
  logLines: string[];
  /** Real-time metric points grouped by name */
  metrics: Map<string, MetricPoint[]>;
  /** Whether the SSE connection is active */
  isConnected: boolean;
  /** Whether the experiment is done (no more events expected) */
  isDone: boolean;
}

/**
 * Hook that connects to the SSE endpoint for real-time experiment events.
 *
 * Maintains separate lists for activities, logs, and metrics.
 * Batches updates to prevent chart jank.
 * Automatically disconnects when experiment completes.
 */
export function useExperimentEvents(
  experimentId: string | null,
  enabled: boolean = true,
): ExperimentEvents {
  const [activities, setActivities] = useState<AgentActivity[]>([]);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [metrics, setMetrics] = useState<Map<string, MetricPoint[]>>(
    new Map(),
  );
  const [isConnected, setIsConnected] = useState(false);
  const [isDone, setIsDone] = useState(false);

  // Use refs for batching
  const pendingActivities = useRef<AgentActivity[]>([]);
  const pendingLogs = useRef<string[]>([]);
  const pendingMetrics = useRef<MetricPoint[]>([]);
  const flushTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const flush = useCallback(() => {
    if (pendingActivities.current.length > 0) {
      const batch = [...pendingActivities.current];
      pendingActivities.current = [];
      setActivities((prev) => [...prev, ...batch]);
    }
    if (pendingLogs.current.length > 0) {
      const batch = [...pendingLogs.current];
      pendingLogs.current = [];
      setLogLines((prev) => [...prev, ...batch]);
    }
    if (pendingMetrics.current.length > 0) {
      const batch = [...pendingMetrics.current];
      pendingMetrics.current = [];
      setMetrics((prev) => {
        const next = new Map(prev);
        for (const point of batch) {
          const key = point.name;
          const existing = next.get(key) ?? [];
          // Window to last 200 points per metric
          const updated = [...existing, point].slice(-200);
          next.set(key, updated);
        }
        return next;
      });
    }
    flushTimer.current = null;
  }, []);

  const scheduleFlush = useCallback(() => {
    if (!flushTimer.current) {
      flushTimer.current = setTimeout(flush, 300);
    }
  }, [flush]);

  useEffect(() => {
    if (!experimentId || !enabled) return;

    // Reset state for new experiment
    setActivities([]);
    setLogLines([]);
    setMetrics(new Map());
    setIsConnected(false);
    setIsDone(false);

    const source = createExperimentEventSource(experimentId);
    let hasOpened = false;

    source.onopen = () => {
      hasOpened = true;
      setIsConnected(true);
    };
    source.onerror = () => {
      setIsConnected(false);
      // If the connection never opened, the endpoint likely returned an HTTP
      // error (e.g. 404). Close to prevent the browser's auto-reconnect loop.
      if (!hasOpened) {
        source.close();
      }
    };

    source.addEventListener("phase_change", (e: MessageEvent) => {
      const event: ProgressEvent = JSON.parse(e.data);
      pendingActivities.current.push({
        agent: "sklearn",
        action: `Phase: ${event.data.phase ?? "unknown"}`,
        timestamp: event.timestamp,
        details: event.data.message as string | undefined,
        data: event.data,
      });
      scheduleFlush();
    });

    source.addEventListener("agent_activity", (e: MessageEvent) => {
      const event: ProgressEvent = JSON.parse(e.data);
      pendingActivities.current.push({
        agent: "sklearn",
        action: (event.data.action as string) ?? "activity",
        timestamp: event.timestamp,
        details: event.data.decision as string | undefined,
        data: event.data,
      });
      scheduleFlush();
    });

    source.addEventListener("metric_update", (e: MessageEvent) => {
      const event: ProgressEvent = JSON.parse(e.data);
      pendingMetrics.current.push({
        name: event.data.name as string,
        value: event.data.value as number,
        step: (event.data.step as number) ?? null,
        timestamp: event.timestamp,
      });
      scheduleFlush();
    });

    source.addEventListener("log_output", (e: MessageEvent) => {
      const event: ProgressEvent = JSON.parse(e.data);
      pendingLogs.current.push(event.data.line as string);
      scheduleFlush();
    });

    source.addEventListener("run_started", (e: MessageEvent) => {
      const event: ProgressEvent = JSON.parse(e.data);
      pendingActivities.current.push({
        agent: "sklearn",
        action: "Training started",
        timestamp: event.timestamp,
        details: `Run ${event.data.run_id}`,
        data: event.data,
      });
      scheduleFlush();
    });

    source.addEventListener("run_completed", (e: MessageEvent) => {
      const event: ProgressEvent = JSON.parse(e.data);
      pendingActivities.current.push({
        agent: "sklearn",
        action: `Run ${event.data.status}`,
        timestamp: event.timestamp,
        details: `${event.data.wall_time_seconds}s`,
        data: event.data,
      });
      scheduleFlush();
    });

    source.addEventListener("error", (e: MessageEvent) => {
      try {
        const event: ProgressEvent = JSON.parse(e.data);
        pendingActivities.current.push({
          agent: "sklearn",
          action: "Error",
          timestamp: event.timestamp,
          details: event.data.message as string,
          data: event.data,
        });
        scheduleFlush();
      } catch {
        // SSE connection error, not a data event
      }
    });

    source.addEventListener("experiment_done", (e: MessageEvent) => {
      const event: ProgressEvent = JSON.parse(e.data);
      pendingActivities.current.push({
        agent: "sklearn",
        action: "Experiment complete",
        timestamp: event.timestamp,
        details: `Best model: ${event.data.best_model}`,
        data: event.data,
      });
      flush();
      setIsDone(true);
      source.close();
    });

    return () => {
      source.close();
      if (flushTimer.current) clearTimeout(flushTimer.current);
      setIsConnected(false);
    };
  }, [experimentId, enabled, flush, scheduleFlush]);

  return { activities, logLines, metrics, isConnected, isDone };
}
