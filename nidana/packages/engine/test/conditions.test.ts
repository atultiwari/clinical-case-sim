import { describe, expect, it } from "vitest";
import {
  conditionHolds,
  idMatches,
  replay,
  type ConditionContext,
} from "../src/index.ts";
import { pilot, settings } from "./helpers.ts";

function context(overrides: Partial<ConditionContext> = {}): ConditionContext {
  return {
    released: new Set(),
    findings: [],
    asked: new Set(),
    ordered: new Set(),
    referred: new Set(),
    commit: null,
    ...overrides,
  };
}

describe("idMatches", () => {
  it("matches exact ids and prefixes ending in .*", () => {
    expect(idMatches("RX.CHELATION.*", "RX.CHELATION.SUCCIMER_ORAL")).toBe(
      true,
    );
    expect(idMatches("RX.CHELATION.*", "RX.CHELATIONX")).toBe(false);
    expect(idMatches("LAB.HAEM.CBC", "LAB.HAEM.CBC")).toBe(true);
    expect(idMatches("LAB.HAEM.CBC", "LAB.HAEM.CBC_X")).toBe(false);
  });
});

describe("conditionHolds", () => {
  const ctx = context({
    released: new Set(["L26", "H10"]),
    findings: [{ finding: "FND.X", tests: new Set(["LAB.HAEM.FILM_REVIEW"]) }],
    asked: new Set(["HX.MEDS.SUPPLEMENTS"]),
    ordered: new Set(["LAB.TOX.BLOOD_LEAD", "LAB.HAEM.CBC"]),
    referred: new Set(["REF.TOXICOLOGY"]),
  });

  it.each([
    [{ released_any: ["L26", "Q1"] }, true],
    [{ released_all: ["L26", "Q1"] }, false],
    [{ released_all: ["L26", "H10"] }, true],
    [{ asked_any: ["HX.MEDS.*"] }, true],
    [{ ordered_all: ["LAB.TOX.BLOOD_LEAD", "LAB.HAEM.CBC"] }, true],
    [{ ordered_any: ["LAB.CHEM.COPPER_CAERULOPLASMIN"] }, false],
    [{ referred_any: ["REF.TOXICOLOGY"] }, true],
    [{ finding_released: ["FND.X"] }, true],
    [
      {
        finding_released: {
          findings: ["FND.X"],
          from_tests: ["LAB.HAEM.FILM"],
        },
      },
      false,
    ],
    [
      { finding_released: { findings: ["FND.X"], from_tests: ["LAB.HAEM.*"] } },
      true,
    ],
    [{ finding_released: { findings: ["FND.X"] } }, true],
    [{ finding_released: ["FND.X"], from_tests: ["LAB.BM.*"] }, false],
    [{ not: { released_any: ["L26"] } }, false],
    [
      {
        all: [
          { released_any: ["L26"] },
          { asked_any: ["HX.MEDS.SUPPLEMENTS"] },
        ],
      },
      true,
    ],
    [{ any: [{ released_any: ["Q"] }, { referred_any: ["REF.*"] }] }, true],
    [{ dx_in: ["DX.X"] }, false],
    [{ plan_has: ["ACT.X"] }, false],
  ])("%j is %s during play", (condition, expected) => {
    expect(conditionHolds(condition, ctx)).toBe(expected);
  });

  it("evaluates commit conditions once a commit exists", () => {
    const committed = context({
      commit: {
        dx: "DX.A",
        evidence: ["H10", "L26"],
        plan: ["ACT.STOP_SUSPECTED_SOURCE", "RX.CHELATION.SUCCIMER_ORAL"],
      },
    });
    expect(conditionHolds({ dx_in: ["DX.A"] }, committed)).toBe(true);
    expect(conditionHolds({ evidence_has: ["H10"] }, committed)).toBe(true);
    expect(conditionHolds({ evidence_has: ["H10", "Q"] }, committed)).toBe(
      false,
    );
    expect(conditionHolds({ plan_has: ["RX.CHELATION.*"] }, committed)).toBe(
      true,
    );
    expect(
      conditionHolds({ plan_has_any: ["RX.IRON.*", "ACT.*"] }, committed),
    ).toBe(true);
    const before = ["ACT.STOP_SUSPECTED_SOURCE", "RX.CHELATION.*"] as [
      string,
      string,
    ];
    expect(conditionHolds({ plan_before: before }, committed)).toBe(true);
    const reversed = context({
      commit: {
        dx: "DX.A",
        evidence: [],
        plan: ["RX.CHELATION.X", "ACT.STOP_SUSPECTED_SOURCE"],
      },
    });
    expect(conditionHolds({ plan_before: before }, reversed)).toBe(false);
    const neither = context({
      commit: { dx: "DX.A", evidence: [], plan: ["ACT.OTHER"] },
    });
    expect(conditionHolds({ plan_before: before }, neither)).toBe(true);
  });

  it("reads the encounter's state from a replay", () => {
    const state = replay(pilot(), settings, "standard", [
      { kind: "order", item: "LAB.HAEM.FILM_REVIEW" },
      { kind: "wait" },
    ]);
    expect(state.releases.some((r) => r.source.id === "RP02")).toBe(true);
  });
});
