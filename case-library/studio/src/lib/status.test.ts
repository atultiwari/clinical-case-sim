import { describe, expect, it } from "vitest";

import { caseStatusLabel, caseStatusTone, humanise, reviewStatusTone } from "@/lib/status";

describe("case status", () => {
  it("labels every status in British English", () => {
    expect(["draft", "in_review", "frozen", "retired"].map(caseStatusLabel)).toEqual([
      "Draft",
      "In review",
      "Frozen",
      "Retired",
    ]);
  });

  it("passes unknown statuses through", () => {
    expect(caseStatusLabel("odd")).toBe("odd");
    expect(caseStatusTone("odd")).toBe("neutral");
  });

  it("gives review statuses tones", () => {
    expect(reviewStatusTone("pending")).toBe("warning");
    expect(reviewStatusTone("approved")).toBe("success");
    expect(reviewStatusTone("rejected")).toBe("danger");
    expect(reviewStatusTone("superseded")).toBe("muted");
  });

  it("humanises ids", () => {
    expect(humanise("low_yield")).toBe("low yield");
  });
});
