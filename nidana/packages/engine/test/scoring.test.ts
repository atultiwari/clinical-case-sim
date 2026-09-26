import { describe, expect, it } from "vitest";
import {
  applyAction,
  replay,
  scoreEncounter,
  type Action,
  type Difficulty,
  type EncounterState,
} from "../src/index.ts";
import { pilot, readConformance, scoring, settings } from "./helpers.ts";

/** The pilot's benchmark path (ANALYSIS.md §10), without its commit. */
const benchmark = (
  readConformance("PMC12949993/benchmark-path.json") as { actions: Action[] }
).actions;

const PLAN = [
  "ACT.STOP_SUSPECTED_SOURCE",
  "RX.CHELATION.SUCCIMER_ORAL",
  "ACT.NOTIFY_PUBLIC_HEALTH",
  "ACT.REPEAT_BLOOD_LEAD",
];

function commit(dx: string, evidence: string[], plan: string[] = PLAN): Action {
  return { kind: "commit", dx, evidence, plan };
}

function play(
  actions: readonly Action[],
  difficulty: Difficulty = "standard",
): EncounterState {
  return replay(pilot(), settings, difficulty, actions);
}

function score(actions: readonly Action[]) {
  return scoreEncounter(pilot(), settings, scoring, play(actions));
}

describe("scoring the pilot (N1.3 acceptance)", () => {
  it("the benchmark path citing the supplement scores diagnosis 5 with every must-do met", () => {
    const result = score([
      ...benchmark,
      commit("DX.LEAD_POISONING", ["H10", "L26"]),
    ]);
    expect(result.diagnosis.anchor).toBe(5);
    expect(result.diagnosis.points).toBe(40);
    expect(result.mustDo.filter((m) => !m.met).map((m) => m.text)).toEqual([]);
    expect(result.management.points).toBe(30);
    expect(result.safety.violations).toEqual([]);
  });

  it("the same path without citing H10 scores diagnosis 4", () => {
    const result = score([...benchmark, commit("DX.LEAD_POISONING", ["L26"])]);
    expect(result.diagnosis.anchor).toBe(4);
    expect(result.diagnosis.points).toBe(30);
  });

  it("a plan with high-dose steroids registers a must-not-do and triggers the cap", () => {
    const result = score([
      ...benchmark,
      commit(
        "DX.LEAD_POISONING",
        ["H10", "L26"],
        [...PLAN, "RX.STEROID.HIGH_DOSE"],
      ),
    ]);
    expect(result.safety.violations).toHaveLength(1);
    expect(result.safety.capApplied).toBe(true);
    expect(result.total).toBeLessThanOrEqual(scoring.safety.cap_total);
  });

  it("a player who asks only the generic toxin question never releases H10 and cannot score 5", () => {
    const actions: Action[] = [
      { kind: "ask", item: "HX.EXPOSURE.TOXINS" },
      { kind: "order", item: "LAB.TOX.BLOOD_LEAD" },
      { kind: "wait" },
    ];
    const state = play(actions);
    expect(state.releases.some((r) => r.source.id === "H10")).toBe(false);
    const refused = applyAction(
      pilot(),
      settings,
      state,
      commit("DX.LEAD_POISONING", ["H10", "L26"]),
    );
    expect(refused.ok ? undefined : refused.error.code).toBe(
      "evidence_not_released",
    );
    const best = score([
      ...actions,
      commit("DX.LEAD_POISONING", ["H09", "L26"]),
    ]);
    expect(best.diagnosis.anchor).toBe(4);
  });

  it("committing to MDS with ring sideroblasts without a blood lead or copper scores 2 with a violation", () => {
    const actions: Action[] = [
      { kind: "order", item: "LAB.HAEM.CBC" },
      { kind: "wait" },
      commit("DX.MDS_RING_SIDEROBLASTS", ["S01.d0"], []),
    ];
    const result = score(actions);
    expect(result.diagnosis.anchor).toBe(2);
    expect(result.safety.violations.map((v) => v.text)).toEqual([
      expect.stringMatching(/^Label myelodysplasia/),
    ]);
  });
});

describe("score components", () => {
  const full = score([
    ...benchmark,
    commit("DX.LEAD_POISONING", ["H10", "L26"]),
  ]);

  it("adds the components, and records the scoring version", () => {
    const sum =
      full.diagnosis.points +
      full.management.points +
      full.efficiency.points +
      full.reasoning.points;
    expect(full.total).toBeCloseTo(sum, 5);
    expect(full.version).toBe(scoring.version);
    expect(full.total).toBeLessThanOrEqual(100);
  });

  it("gives full cost marks when spending no more than the efficient path", () => {
    expect(full.efficiency.cost).toBe(scoring.efficiency.cost_points);
  });

  it("gives partial management marks for partly met must-dos", () => {
    const result = score([
      ...benchmark,
      commit("DX.LEAD_POISONING", ["H10"], ["ACT.REPEAT_BLOOD_LEAD"]),
    ]);
    const met = result.mustDo.filter((m) => m.met).length;
    expect(result.management.points).toBeCloseTo(
      (30 * met) / result.mustDo.length,
      5,
    );
    expect(met).toBeLessThan(result.mustDo.length);
  });

  it("credits the true diagnosis in the final differential", () => {
    const withDifferential = score([
      ...benchmark,
      { kind: "differential", items: ["DX.WARM_AIHA", "DX.LEAD_POISONING"] },
      commit("DX.LEAD_POISONING", ["H10", "L26"]),
    ]);
    expect(withDifferential.reasoning.differential).toBe(
      scoring.reasoning.differential_points,
    );
    expect(full.reasoning.differential).toBe(0);
  });

  it("penalises unnecessary tests", () => {
    const unnecessary =
      pilot().bundle.test_utility.find((t) => t.utility === "unnecessary")
        ?.test_item_id ?? "";
    const result = score([
      { kind: "order", item: unnecessary },
      commit("DX.LEAD_POISONING", []),
    ]);
    expect(result.efficiency.tests).toBe(
      scoring.efficiency.test_points -
        scoring.efficiency.unnecessary_test_penalty,
    );
  });

  it("never goes below zero", () => {
    const harmful = score([
      commit(
        "DX.WARM_AIHA",
        [],
        ["RX.STEROID.HIGH_DOSE", "RX.IRON.ORAL", "RX.CHELATION.SUCCIMER_ORAL"],
      ),
    ]);
    expect(harmful.safety.violations.length).toBeGreaterThanOrEqual(3);
    expect(harmful.total).toBe(0);
  });
});

describe("commit", () => {
  const state = play(benchmark);
  const code = (
    action: unknown,
    from: EncounterState = state,
  ): string | undefined => {
    const result = applyAction(pilot(), settings, from, action);
    return result.ok ? undefined : result.error.code;
  };

  it("checks the diagnosis, the evidence and the plan", () => {
    expect(code(commit("LAB.HAEM.CBC", []))).toBe("wrong_kind");
    expect(code(commit("DX.LEAD_POISONING", ["NOPE"]))).toBe(
      "evidence_not_released",
    );
    expect(code(commit("DX.LEAD_POISONING", [], ["LAB.HAEM.CBC"]))).toBe(
      "wrong_kind",
    );
    expect(
      code(
        commit("DX.LEAD_POISONING", [
          "H10",
          "L26",
          "H03",
          "H04",
          "H08",
          "RP02",
        ]),
      ),
    ).toBe("invalid_action");
  });

  it("closes the encounter", () => {
    const done = play([...benchmark, commit("DX.LEAD_POISONING", ["H10"])]);
    expect(done.commit).toEqual({
      at: done.clock,
      dx: "DX.LEAD_POISONING",
      evidence: ["H10"],
      plan: PLAN,
      note: null,
    });
    expect(code({ kind: "ask", item: "HX.MEDS.CURRENT" }, done)).toBe(
      "committed",
    );
    expect(code(commit("DX.LEAD_POISONING", []), done)).toBe("committed");
  });

  it("is accepted after a limit forces it", () => {
    const forced = play([{ kind: "wait", minutes: 20_000 }]);
    expect(forced.mustCommit).toBe("max_stay");
    expect(code(commit("DX.LEAD_POISONING", []), forced)).toBeUndefined();
  });

  it("cannot be scored before it happens", () => {
    expect(() => scoreEncounter(pilot(), settings, scoring, state)).toThrow(
      /not been committed/,
    );
  });
});
