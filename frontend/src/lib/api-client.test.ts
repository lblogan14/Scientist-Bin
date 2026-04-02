import { describe, it, expect } from "vitest";
import { extractErrorMessage } from "./api-client";

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
