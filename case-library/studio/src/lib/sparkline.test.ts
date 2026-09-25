import { describe, expect, it } from "vitest";

import { sparkline } from "@/lib/sparkline";

const size = { width: 100, height: 20, padding: 0 };

describe("sparkline", () => {
  it("returns null for no points", () => {
    expect(sparkline([], size)).toBeNull();
  });

  it("scales x by day and y by value (high values at the top)", () => {
    const geometry = sparkline(
      [
        { day: 0, value: 10, flag: null },
        { day: 4, value: 20, flag: "H" },
        { day: 1, value: 15, flag: null },
      ],
      size,
    );
    expect(geometry?.path).toBe("M0 20 L25 10 L100 0");
    expect(geometry?.min).toBe(10);
    expect(geometry?.max).toBe(20);
    expect(geometry?.dots[2]).toMatchObject({ day: 4, flag: "H" });
  });

  it("draws a flat series at mid-height", () => {
    const geometry = sparkline(
      [
        { day: 0, value: 5, flag: null },
        { day: 1, value: 5, flag: null },
      ],
      size,
    );
    expect(geometry?.path).toBe("M0 10 L100 10");
  });

  it("centres a single day", () => {
    expect(sparkline([{ day: 3, value: 1, flag: null }], size)?.path).toBe("M50 10");
  });
});
