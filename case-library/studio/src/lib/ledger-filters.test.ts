import { describe, expect, it } from "vitest";

import { hasActiveFilters, judgementValue, ledgerQuery, parseLedgerFilters } from "@/lib/ledger-filters";

describe("parseLedgerFilters", () => {
  it("keeps known values and drops unknown ones", () => {
    const filters = parseLedgerFilters({
      tier: "affected",
      priority: "urgent",
      status: ["pending", "approved"],
      judgement: "yes",
      target: "  CMP.HB ",
      page: "3",
    });
    expect(filters).toEqual({
      tier: "affected",
      priority: undefined,
      status: "pending",
      judgement: "yes",
      target: "CMP.HB",
      page: 3,
    });
  });

  it("defaults to no filters on page 1", () => {
    const filters = parseLedgerFilters({ page: "-2" });
    expect(filters.page).toBe(1);
    expect(hasActiveFilters(filters)).toBe(false);
  });

  it("caps the target text", () => {
    expect(parseLedgerFilters({ target: "x".repeat(500) }).target).toHaveLength(100);
  });
});

describe("judgementValue", () => {
  it("maps yes, no and any", () => {
    expect(judgementValue(parseLedgerFilters({ judgement: "yes" }))).toBe(true);
    expect(judgementValue(parseLedgerFilters({ judgement: "no" }))).toBe(false);
    expect(judgementValue(parseLedgerFilters({}))).toBeNull();
  });
});

describe("ledgerQuery", () => {
  const filters = parseLedgerFilters({ tier: "normal", page: "4" });

  it("changes one filter and resets the page", () => {
    expect(ledgerQuery(filters, { status: "pending" })).toBe("?tier=normal&status=pending");
  });

  it("clears a filter", () => {
    expect(ledgerQuery(filters, { tier: undefined })).toBe("");
  });

  it("moves between pages", () => {
    expect(ledgerQuery(filters, { page: 5 })).toBe("?tier=normal&page=5");
  });
});
