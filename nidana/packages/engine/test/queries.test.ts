import { describe, expect, it } from "vitest";
import {
  conditionContext,
  conditionHolds,
  replay,
  valueOf,
} from "../src/index.ts";
import { pilot, settings } from "./helpers.ts";

describe("valueOf", () => {
  it("returns nothing for a component that was never released", () => {
    const state = replay(pilot(), settings, "standard", []);
    expect(valueOf(pilot(), state, "CMP.HB")).toBeUndefined();
  });

  it("reads a ledger value as text", () => {
    const state = replay(pilot(), settings, "standard", [
      { kind: "order", item: "LAB.HAEM.CBC" },
      { kind: "wait" },
    ]);
    const rdw = valueOf(pilot(), state, "CMP.RDW");
    expect(rdw?.release.source.table).toBe("ledger");
    expect(rdw?.value).toMatch(/^\d/);
  });

  it("reads a qualitative ledger answer from its text", () => {
    const qualitative = pilot().bundle.ledger.find(
      (row) =>
        row.target.startsWith("CMP.") &&
        typeof row.value.text === "string" &&
        row.value.value === undefined,
    );
    expect(qualitative).toBeDefined();
    const test = pilot().catalogue.tests.find((t) =>
      t.components.includes(qualitative?.target ?? ""),
    );
    const state = replay(pilot(), settings, "guided", [
      { kind: "order", item: test?.item_id ?? "" },
      { kind: "wait", minutes: 5000 },
    ]);
    const found = valueOf(pilot(), state, qualitative?.target ?? "");
    expect(typeof found?.value).toBe("string");
  });
});

describe("resultsForTest", () => {
  it("says so when a test has nothing to return", async () => {
    const { resultsForTest } = await import("../src/index.ts");
    const prepared = pilot();
    const tests = new Map(prepared.tests);
    const cbc = tests.get("LAB.HAEM.CBC");
    if (cbc !== undefined)
      tests.set("LAB.HAEM.CBC", { ...cbc, components: [] });
    const drafts = resultsForTest(
      { ...prepared, tests },
      "LAB.HAEM.CBC",
      0,
      settings.difficulties.standard,
    );
    expect(drafts.map((d) => d.source)).toEqual([
      { table: "none", id: "LAB.HAEM.CBC" },
    ]);
  });
});

describe("conditionContext", () => {
  it("records findings with both the ordered test and the report's own test", () => {
    const state = replay(pilot(), settings, "guided", [
      { kind: "order", item: "LAB.HAEM.FILM" },
      { kind: "wait" },
    ]);
    const ctx = conditionContext(pilot(), state);
    const stippling = ctx.findings.find(
      (f) => f.finding === "FND.COARSE_BASOPHILIC_STIPPLING",
    );
    expect([...(stippling?.tests ?? [])].sort()).toEqual([
      "LAB.HAEM.FILM",
      "LAB.HAEM.FILM_REVIEW",
    ]);
    expect(conditionHolds({ finding_released: ["FND.*"] }, ctx)).toBe(true);
  });

  it("treats a null condition as met and refuses an unknown keyword", () => {
    const ctx = conditionContext(
      pilot(),
      replay(pilot(), settings, "standard", []),
    );
    expect(conditionHolds(null, ctx)).toBe(true);
    expect(() => conditionHolds({ asked_all: ["X"] } as never, ctx)).toThrow(
      /asked_all/,
    );
  });
});
