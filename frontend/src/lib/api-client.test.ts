import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  extractErrorMessage,
  submitTrainRequest,
  listExperiments,
  getExperiment,
  deleteExperiment,
  checkHealth,
  getArtifactDownloadUrl,
  getModelDownloadUrl,
  getResultsDownloadUrl,
  getExperimentPlan,
  getExperimentAnalysis,
  getExperimentSummary,
} from "./api-client";

// ---------------------------------------------------------------------------
// Mock ky — vi.hoisted ensures these are available when vi.mock runs
// ---------------------------------------------------------------------------

const { mockJson, mockPost, mockGet, mockDelete } = vi.hoisted(() => {
  const mockJson = vi.fn();
  const mockPost = vi.fn(() => ({ json: mockJson }));
  const mockGet = vi.fn(() => ({ json: mockJson }));
  const mockDelete = vi.fn(() => Promise.resolve());
  return { mockJson, mockPost, mockGet, mockDelete };
});

vi.mock("ky", () => ({
  default: {
    create: () => ({
      post: mockPost,
      get: mockGet,
      delete: mockDelete,
    }),
  },
}));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("extractErrorMessage", () => {
  it("extracts detail from HTTPError-like response", async () => {
    const error = {
      response: new Response(JSON.stringify({ detail: "Data file not found" }), {
        status: 400,
      }),
    };
    const msg = await extractErrorMessage(error);
    expect(msg).toBe("Data file not found");
  });

  it("falls back to status code when no JSON body", async () => {
    const error = {
      response: new Response("not json", { status: 500 }),
    };
    const msg = await extractErrorMessage(error);
    expect(msg).toBe("Request failed (500)");
  });

  it("extracts message from standard Error", async () => {
    const msg = await extractErrorMessage(new Error("Network timeout"));
    expect(msg).toBe("Network timeout");
  });

  it("returns default message for unknown error type", async () => {
    const msg = await extractErrorMessage("something weird");
    expect(msg).toBe("An unexpected error occurred");
  });

  it("returns default for null", async () => {
    const msg = await extractErrorMessage(null);
    expect(msg).toBe("An unexpected error occurred");
  });
});

describe("submitTrainRequest", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends POST to 'train' with the request body and returns experiment", async () => {
    const fakeExperiment = { id: "exp-1", objective: "Classify iris" };
    mockJson.mockResolvedValueOnce(fakeExperiment);

    const request = {
      objective: "Classify iris species",
      data_description: "150 samples, 4 features",
    };
    const result = await submitTrainRequest(request);

    expect(mockPost).toHaveBeenCalledWith("train", { json: request });
    expect(result).toEqual(fakeExperiment);
  });

  it("passes auto_approve_plan when provided", async () => {
    mockJson.mockResolvedValueOnce({ id: "exp-2" });

    const request = {
      objective: "Classify iris species",
      auto_approve_plan: true,
    };
    await submitTrainRequest(request);

    expect(mockPost).toHaveBeenCalledWith("train", { json: request });
  });
});

describe("listExperiments", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends GET to 'experiments' with no params when none provided", async () => {
    const fakeData = { experiments: [], total: 0, offset: 0, limit: 20 };
    mockJson.mockResolvedValueOnce(fakeData);

    const result = await listExperiments();

    expect(mockGet).toHaveBeenCalledWith("experiments", { searchParams: {} });
    expect(result).toEqual(fakeData);
  });

  it("passes status, framework, search params", async () => {
    const fakeData = { experiments: [], total: 0, offset: 0, limit: 20 };
    mockJson.mockResolvedValueOnce(fakeData);

    await listExperiments({
      status: "completed",
      framework: "sklearn",
      search: "iris",
    });

    expect(mockGet).toHaveBeenCalledWith("experiments", {
      searchParams: {
        status: "completed",
        framework: "sklearn",
        search: "iris",
      },
    });
  });

  it("passes offset and limit as strings", async () => {
    const fakeData = { experiments: [], total: 50, offset: 10, limit: 5 };
    mockJson.mockResolvedValueOnce(fakeData);

    await listExperiments({ offset: 10, limit: 5 });

    expect(mockGet).toHaveBeenCalledWith("experiments", {
      searchParams: { offset: "10", limit: "5" },
    });
  });

  it("omits undefined params", async () => {
    mockJson.mockResolvedValueOnce({ experiments: [], total: 0, offset: 0, limit: 20 });

    await listExperiments({ status: "running" });

    expect(mockGet).toHaveBeenCalledWith("experiments", {
      searchParams: { status: "running" },
    });
  });
});

describe("getExperiment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends GET to 'experiments/{id}' and returns experiment", async () => {
    const fakeExperiment = { id: "exp-123", objective: "Classify" };
    mockJson.mockResolvedValueOnce(fakeExperiment);

    const result = await getExperiment("exp-123");

    expect(mockGet).toHaveBeenCalledWith("experiments/exp-123");
    expect(result).toEqual(fakeExperiment);
  });
});

describe("deleteExperiment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends DELETE to 'experiments/{id}'", async () => {
    await deleteExperiment("exp-456");

    expect(mockDelete).toHaveBeenCalledWith("experiments/exp-456");
  });
});

describe("checkHealth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends GET to 'health' and returns health response", async () => {
    const fakeHealth = { status: "ok" as const };
    mockJson.mockResolvedValueOnce(fakeHealth);

    const result = await checkHealth();

    expect(mockGet).toHaveBeenCalledWith("health");
    expect(result).toEqual({ status: "ok" });
  });
});

describe("getArtifactDownloadUrl", () => {
  it("constructs the correct URL for model artifact", () => {
    const url = getArtifactDownloadUrl("exp-123", "model");
    expect(url).toBe("/api/v1/experiments/exp-123/artifacts/model");
  });

  it("constructs the correct URL for results artifact", () => {
    const url = getArtifactDownloadUrl("exp-123", "results");
    expect(url).toBe("/api/v1/experiments/exp-123/artifacts/results");
  });

  it("constructs the correct URL for charts artifact", () => {
    const url = getArtifactDownloadUrl("exp-123", "charts");
    expect(url).toBe("/api/v1/experiments/exp-123/artifacts/charts");
  });

  it("constructs the correct URL for journal artifact", () => {
    const url = getArtifactDownloadUrl("exp-abc", "journal");
    expect(url).toBe("/api/v1/experiments/exp-abc/artifacts/journal");
  });
});

describe("getModelDownloadUrl", () => {
  it("returns model artifact URL", () => {
    expect(getModelDownloadUrl("exp-1")).toBe(
      "/api/v1/experiments/exp-1/artifacts/model",
    );
  });
});

describe("getResultsDownloadUrl", () => {
  it("returns results artifact URL", () => {
    expect(getResultsDownloadUrl("exp-1")).toBe(
      "/api/v1/experiments/exp-1/artifacts/results",
    );
  });
});

describe("getExperimentPlan", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends GET to 'experiments/{id}/plan' and returns plan data", async () => {
    const fakePlan = { execution_plan: { approach_summary: "Try RF" } };
    mockJson.mockResolvedValueOnce(fakePlan);

    const result = await getExperimentPlan("exp-789");

    expect(mockGet).toHaveBeenCalledWith("experiments/exp-789/plan");
    expect(result).toEqual(fakePlan);
  });

  it("handles null execution_plan", async () => {
    mockJson.mockResolvedValueOnce({ execution_plan: null });

    const result = await getExperimentPlan("exp-empty");

    expect(result.execution_plan).toBeNull();
  });
});

describe("getExperimentAnalysis", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends GET to 'experiments/{id}/analysis' and returns analysis data", async () => {
    const fakeAnalysis = {
      analysis_report: "# Report\nSome analysis",
      split_data_paths: { train: "/data/train.csv", val: "/data/val.csv" },
    };
    mockJson.mockResolvedValueOnce(fakeAnalysis);

    const result = await getExperimentAnalysis("exp-100");

    expect(mockGet).toHaveBeenCalledWith("experiments/exp-100/analysis");
    expect(result).toEqual(fakeAnalysis);
  });

  it("handles null analysis report", async () => {
    mockJson.mockResolvedValueOnce({
      analysis_report: null,
      split_data_paths: null,
    });

    const result = await getExperimentAnalysis("exp-empty");

    expect(result.analysis_report).toBeNull();
    expect(result.split_data_paths).toBeNull();
  });
});

describe("getExperimentSummary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends GET to 'experiments/{id}/summary' and returns summary data", async () => {
    const fakeSummary = { summary_report: "# Summary\nGreat results" };
    mockJson.mockResolvedValueOnce(fakeSummary);

    const result = await getExperimentSummary("exp-200");

    expect(mockGet).toHaveBeenCalledWith("experiments/exp-200/summary");
    expect(result).toEqual(fakeSummary);
  });

  it("handles null summary report", async () => {
    mockJson.mockResolvedValueOnce({ summary_report: null });

    const result = await getExperimentSummary("exp-empty");

    expect(result.summary_report).toBeNull();
  });
});
