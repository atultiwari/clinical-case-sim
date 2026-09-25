import { describe, expect, it } from "vitest";

import { formatRefRanges } from "@/lib/ref-ranges";

describe("formatRefRanges", () => {
  it("formats sex- and age-specific ranges with the unit", () => {
    expect(
      formatRefRanges(
        [
          { sex: "F", low: 115, high: 165 },
          { sex: "M", age_min: 18, age_max: 65, low: 130, high: 180 },
          { low: 0, high: 5 },
          { sex: "any", age_min: 70, high: 10 },
        ],
        "g/L",
      ),
    ).toEqual(["F: 115–165 g/L", "M, 18–65 y: 130–180 g/L", "0–5 g/L", "≥ 70 y: ≤ 10 g/L"]);
  });

  it("handles missing or odd values", () => {
    expect(formatRefRanges(null)).toEqual([]);
    expect(formatRefRanges([{ sex: "F" }, 3])).toEqual(["F: no range", "3"]);
  });
});
