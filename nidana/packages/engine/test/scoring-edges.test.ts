import { describe, expect, it } from "vitest";
import {
  applyAction,
  buildDebrief,
  groundTruthOf,
  parseScoringSettings,
  replay,
  scoreEncounter,
  type Action,
  type PreparedCase,
} from "../src/index.ts";
import { pilot, scoring, settings } from "./helpers.ts";

const commit = (dx: string, plan: string[] = []): Action => ({
  kind: "commit",
  dx,
  evidence: [],
  plan,
});

function withTruth(changes: Record<string, unknown>): PreparedCase {
  const prepared = pilot();
  return {
    ...prepared,
    bundle: {
      ...prepared.bundle,
      ground_truth: { ...prepared.bundle.ground_truth, ...changes },
    },
  };
}

function scoreWith(prepared: PreparedCase, actions: Action[]) {
  return scoreEncounter(
    prepared,
    settings,
    scoring,
    replay(prepared, settings, "standard", actions),
  );
}

describe("ground truth the engine cannot score", () => {
  it("refuses a rubric without anchors", () => {
    expect(() => groundTruthOf(withTruth({ rubric: { rubric: [] } }))).toThrow(
      /cannot be scored/,
    );
    expect(() => groundTruthOf(withTruth({ final_dx: { name: "x" } }))).toThrow(
      /cannot be scored/,
    );
  });

  it("reports schema 0.2 plain-text rules as not evaluable and scores the rest", () => {
    const prepared = withTruth({
      must_do: ["Take a history"],
      must_not_do: ["Do harm"],
    });
    const result = scoreWith(prepared, [commit("DX.LEAD_POISONING")]);
    expect(result.mustDo).toEqual([{ text: "Take a history", met: null }]);
    expect(result.management.points).toBe(scoring.management.points);
    expect(result.safety.violations).toEqual([]);
  });
});

describe("efficiency and reasoning edges", () => {
  it("scales cost marks down when spending more than the efficient path", () => {
    const prepared = { ...pilot(), efficientPathCost: 300 };
    const result = scoreWith(prepared, [
      { kind: "order", item: "LAB.HAEM.CBC" },
      { kind: "order", item: "LAB.HAEM.FILM" },
      commit("DX.LEAD_POISONING"),
    ]);
    expect(result.efficiency.cost).toBeCloseTo(
      (scoring.efficiency.cost_points * 300) / 400,
      5,
    );
  });

  it("scales time marks down for a late commit", () => {
    const result = scoreWith(pilot(), [
      { kind: "wait", minutes: 9000 },
      commit("DX.LEAD_POISONING"),
    ]);
    expect(result.efficiency.time).toBeLessThan(scoring.efficiency.time_points);
    expect(result.efficiency.time).toBeGreaterThan(0);
  });

  it("penalises a referral on no path of the case", () => {
    const result = scoreWith(pilot(), [
      { kind: "refer", item: "REF.DENTISTRY" },
      commit("DX.LEAD_POISONING"),
    ]);
    const efficientReferrals =
      pilot()
        .bundle.path_analysis.find((p) => p.kind === "efficient")
        ?.items.filter((id) => id.startsWith("REF.")).length ?? 0;
    const expected =
      scoring.reasoning.referral_points -
      scoring.reasoning.referral_penalty * (1 + efficientReferrals);
    expect(result.reasoning.referrals).toBe(Math.max(0, expected));
  });

  it("penalises risky tests more than unnecessary ones", () => {
    const prepared = {
      ...pilot(),
      bundle: {
        ...pilot().bundle,
        test_utility: [
          {
            test_item_id: "PROC.BM.ASPIRATE",
            utility: "risky" as const,
            rationale: null,
          },
        ],
      },
    };
    const result = scoreWith(prepared, [
      { kind: "order", item: "PROC.BM.ASPIRATE" },
      commit("DX.LEAD_POISONING"),
    ]);
    expect(result.efficiency.tests).toBe(
      scoring.efficiency.test_points - scoring.efficiency.risky_test_penalty,
    );
  });

  it("gives full discriminator marks when the case marks none", () => {
    const prepared = {
      ...pilot(),
      bundle: {
        ...pilot().bundle,
        facts: pilot().bundle.facts.map((f) => ({ ...f, pivotal: false })),
        test_utility: [],
      },
    };
    expect(
      scoreWith(prepared, [commit("DX.LEAD_POISONING")]).reasoning
        .discriminators,
    ).toBe(scoring.reasoning.discriminator_points);
  });
});

describe("commit and debrief edges", () => {
  it("refuses a diagnosis the catalogue does not have", () => {
    const result = applyAction(
      pilot(),
      settings,
      replay(pilot(), settings, "standard", []),
      commit("DX.NOPE"),
    );
    expect(result.ok ? undefined : result.error.code).toBe("unknown_item");
  });

  it("has no attribution for a de novo case", () => {
    const prepared = {
      ...pilot(),
      bundle: { ...pilot().bundle, source: null },
    };
    const state = replay(prepared, settings, "standard", [
      commit("DX.LEAD_POISONING"),
    ]);
    expect(
      buildDebrief(prepared, settings, scoring, state).attribution,
    ).toBeNull();
  });

  it("refuses invalid scoring settings with the field named", () => {
    expect(() => parseScoringSettings({ ...scoring, version: "" })).toThrow(
      /version/,
    );
  });
});
