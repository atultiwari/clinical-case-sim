import { describe, expect, it } from "vitest";
import {
  EngineError,
  applyAction,
  initialState,
  replay,
  type Action,
  type EncounterState,
} from "../src/index.ts";
import { pilot, settings } from "./helpers.ts";

const DAY = 1440;

function start(
  difficulty: "guided" | "standard" | "expert" = "standard",
): EncounterState {
  return initialState(pilot(), settings, difficulty);
}

function errorCode(
  action: unknown,
  state: EncounterState = start(),
): string | undefined {
  const result = applyAction(pilot(), settings, state, action);
  return result.ok ? undefined : result.error.code;
}

describe("action validation", () => {
  it("refuses an item the catalogue does not have", () => {
    expect(errorCode({ kind: "ask", item: "HX.NOT.AN_ITEM" })).toBe(
      "unknown_item",
    );
  });

  it("refuses an item of the wrong kind for the action", () => {
    expect(errorCode({ kind: "order", item: "HX.MEDS.CURRENT" })).toBe(
      "wrong_kind",
    );
    expect(errorCode({ kind: "ask", item: "LAB.HAEM.CBC" })).toBe("wrong_kind");
    expect(errorCode({ kind: "refer", item: "EX.GEN.PALLOR" })).toBe(
      "wrong_kind",
    );
  });

  it("refuses items the Attending seat cannot use", () => {
    expect(errorCode({ kind: "examine", item: "EX.EYE.SLIT_LAMP" })).toBe(
      "not_available_to_seat",
    );
  });

  it("refuses a test the catalogue lists without a price or turnaround", () => {
    const prepared = pilot();
    const tests = new Map(prepared.tests);
    tests.delete("LAB.HAEM.CBC");
    const broken = { ...prepared, tests };
    const result = applyAction(broken, settings, start(), {
      kind: "order",
      item: "LAB.HAEM.CBC",
    });
    expect(result.ok ? undefined : result.error.code).toBe("not_orderable");
  });

  it("refuses a malformed action with a clear message", () => {
    const result = applyAction(pilot(), settings, start(), {
      kind: "shout",
      item: "x",
    });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("invalid_action");
      expect(result.error.message).toContain("kind");
    }
    expect(errorCode({ kind: "wait", minutes: 0 })).toBe("invalid_action");
  });

  it("accepts a differential of diagnoses only", () => {
    const ok = applyAction(pilot(), settings, start(), {
      kind: "differential",
      items: ["DX.WARM_AIHA", "DX.MDS_RING_SIDEROBLASTS"],
    });
    expect(ok.ok && ok.state.differential).toEqual([
      { at: 0, items: ["DX.WARM_AIHA", "DX.MDS_RING_SIDEROBLASTS"] },
    ]);
    expect(errorCode({ kind: "differential", items: ["LAB.HAEM.CBC"] })).toBe(
      "wrong_kind",
    );
  });

  it("replay throws on an action the engine refuses, naming its position", () => {
    const actions: Action[] = [
      { kind: "ask", item: "HX.MEDS.CURRENT" },
      { kind: "ask", item: "X.Y" },
    ];
    expect(() => replay(pilot(), settings, "standard", actions)).toThrow(
      EngineError,
    );
    expect(() => replay(pilot(), settings, "standard", actions)).toThrow(
      /action 2/,
    );
  });
});

describe("limits", () => {
  it("sets the budget from the efficient path's tests and the difficulty's factor", () => {
    const standard = start("standard").limits.budget;
    const expert = start("expert").limits.budget;
    const guided = start("guided").limits.budget;
    expect(standard).toBe(Math.round(pilot().efficientPathCost * 1.5));
    expect(expert).toBeLessThan(standard);
    expect(guided).toBeGreaterThan(standard);
  });

  it("refuses an order the remaining budget cannot pay for", () => {
    const state = { ...start(), spend: start().limits.budget - 100 };
    expect(
      errorCode({ kind: "order", item: "LAB.TOX.BLOOD_LEAD" }, state),
    ).toBe("over_budget");
  });

  it("allows as many referrals as the difficulty sets", () => {
    const refer = (item: string): Action => ({ kind: "refer", item });
    const three = [
      refer("REF.TOXICOLOGY"),
      refer("REF.HAEMATOLOGY"),
      refer("REF.NEUROLOGY"),
    ];
    const state = replay(pilot(), settings, "standard", three);
    expect(errorCode(refer("REF.CARDIOLOGY"), state)).toBe("referral_limit");
    expect(() => replay(pilot(), settings, "expert", three)).toThrow(
      /referral_limit/,
    );
  });

  it("forces a commit when the stay reaches its maximum", () => {
    const state = replay(pilot(), settings, "standard", [
      { kind: "wait", minutes: 8 * DAY },
    ]);
    expect(state.clock).toBe(settings.clock.max_stay_minutes);
    expect(state.mustCommit).toBe("max_stay");
    expect(errorCode({ kind: "ask", item: "HX.MEDS.CURRENT" }, state)).toBe(
      "must_commit",
    );
  });

  it("waits to the start of the next day when nothing is pending", () => {
    const state = replay(pilot(), settings, "standard", [
      { kind: "ask", item: "HX.MEDS.CURRENT" },
      { kind: "wait" },
    ]);
    expect(state.clock).toBe(DAY);
  });

  it("delivers results in due order when waiting", () => {
    const state = replay(pilot(), settings, "standard", [
      { kind: "order", item: "LAB.TOX.BLOOD_LEAD" },
      { kind: "order", item: "LAB.HAEM.CBC" },
      { kind: "wait" },
    ]);
    expect(state.clock).toBe(240);
    expect(state.pending.map((p) => p.item)).toEqual(["LAB.TOX.BLOOD_LEAD"]);
  });
});
