import { describe, expect, it } from "vitest";

import { coverageOf, formatCoverage, groupCoverageGaps, summariseCoverage } from "@/lib/coverage";

describe("summariseCoverage", () => {
  it("sums resolved and total across kinds", () => {
    const summary = summariseCoverage([
      { kind: "exam", total: 10, resolved: 10, missing: [] },
      { kind: "test", total: 20, resolved: 13, missing: ["LAB.X"] },
    ]);
    expect(summary).toEqual({ resolved: 23, total: 30, percent: 76.6 });
    expect(formatCoverage(summary)).toBe("23/30 (76.6%)");
  });

  it("never rounds up to 100%", () => {
    expect(coverageOf(999, 1000).percent).toBe(99.9);
    expect(coverageOf(1999, 2000).percent).toBe(99.9);
  });

  it("handles an empty catalogue", () => {
    const summary = summariseCoverage([]);
    expect(summary.percent).toBeNull();
    expect(formatCoverage(summary)).toBe("no active items");
  });
});

describe("groupCoverageGaps", () => {
  it("groups components and days under their item", () => {
    const groups = groupCoverageGaps([
      { kind: "history", item_id: "HX.DIET", component_id: null, day: null },
      { kind: "test", item_id: "LAB.CBC", component_id: "CMP.HB", day: 2 },
      { kind: "test", item_id: "LAB.CBC", component_id: "CMP.HB", day: 0 },
      { kind: "test", item_id: "LAB.CBC", component_id: "CMP.RBC", day: 1 },
    ]);
    expect(groups).toEqual([
      { kind: "history", itemId: "HX.DIET", components: [] },
      {
        kind: "test",
        itemId: "LAB.CBC",
        components: [
          { componentId: "CMP.HB", days: [0, 2] },
          { componentId: "CMP.RBC", days: [1] },
        ],
      },
    ]);
  });
});
