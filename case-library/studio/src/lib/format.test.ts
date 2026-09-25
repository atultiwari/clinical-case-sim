import { describe, expect, it } from "vitest";

import { formatDate, formatDateTime, formatDay, formatPrice, formatTurnaround } from "@/lib/format";

describe("format", () => {
  it("formats turnaround", () => {
    expect(formatTurnaround(null)).toBe("—");
    expect(formatTurnaround(45)).toBe("45 min");
    expect(formatTurnaround(120)).toBe("2 h");
    expect(formatTurnaround(90)).toBe("1 h 30 min");
    expect(formatTurnaround(2880)).toBe("2 d");
  });

  it("formats rupee prices", () => {
    expect(formatPrice(1200)).toBe("₹1,200");
    expect(formatPrice(null)).toBe("—");
  });

  it("formats dates in British style", () => {
    expect(formatDate(new Date("2022-07-13T00:00:00Z"))).toBe("13 Jul 2022");
    expect(formatDate(null)).toBe("—");
    expect(formatDate("not a date")).toBe("—");
    expect(formatDateTime("2026-09-25T10:05:00Z")).toMatch(/^25 Sept? 2026,? 10:05 UTC$/);
  });

  it("formats days", () => {
    expect(formatDay(null)).toBe("All admission");
    expect(formatDay(3)).toBe("Day 3");
  });
});
