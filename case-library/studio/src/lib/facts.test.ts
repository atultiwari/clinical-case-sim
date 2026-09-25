import { describe, expect, it } from "vitest";

import { groupFacts } from "@/lib/facts";
import type { FactRow } from "@/lib/types";

function fact(overrides: Partial<FactRow> & Pick<FactRow, "id">): FactRow {
  return {
    category: "Laboratory",
    item: "Haemoglobin",
    catalogue_ref: "CMP.HB",
    value: null,
    value_num: null,
    unit: "g/L",
    ref_range: null,
    flag: null,
    day: null,
    kind: "raw",
    origin: "article",
    formula: null,
    reveals_dx: false,
    pivotal: false,
    release: "chart",
    source_locator: "Table 1",
    review_status: "pending",
    ...overrides,
  };
}

describe("groupFacts", () => {
  it("groups by category then item and builds a series across days", () => {
    const input = [
      fact({ id: "L03", day: 2, value_num: 80, flag: "L" }),
      fact({ id: "L01", day: 0, value_num: 72, flag: "L" }),
      fact({ id: "H01", category: "History", item: "Occupation", catalogue_ref: null, value: "Painter" }),
    ];
    const groups = groupFacts(input);
    expect(groups.map((g) => g.category)).toEqual(["Laboratory", "History"]);
    const hb = groups[0]?.items[0];
    expect(hb?.key).toBe("CMP.HB");
    expect(hb?.rows.map((r) => r.id)).toEqual(["L01", "L03"]);
    expect(hb?.series).toEqual([
      { day: 0, value: 72, flag: "L" },
      { day: 2, value: 80, flag: "L" },
    ]);
    expect(groups[1]?.items[0]).toMatchObject({ key: "item:Occupation", label: "Occupation", series: null });
  });

  it("does not draw a series for a single day", () => {
    const groups = groupFacts([fact({ id: "L01", day: 0, value_num: 72 }), fact({ id: "L02", day: 0, value_num: 73 })]);
    expect(groups[0]?.items[0]?.series).toBeNull();
  });

  it("does not change its input", () => {
    const input = [fact({ id: "B", day: 2, value_num: 1 }), fact({ id: "A", day: 1, value_num: 2 })];
    groupFacts(input);
    expect(input.map((f) => f.id)).toEqual(["B", "A"]);
  });

  it("returns nothing for no facts", () => {
    expect(groupFacts([])).toEqual([]);
  });
});
