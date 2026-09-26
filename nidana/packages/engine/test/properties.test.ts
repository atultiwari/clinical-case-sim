import fc from "fast-check";
import { describe, expect, it } from "vitest";
import {
  applyAction,
  initialState,
  replay,
  type Action,
  type EncounterState,
} from "../src/index.ts";
import { pilot, settings } from "./helpers.ts";

const items = (kind: string) =>
  pilot()
    .catalogue.items.filter(
      (i) => i.kind === kind && i.specialty_scope.includes("attending"),
    )
    .map((i) => i.id)
    .slice(0, 60);

const anyAction: fc.Arbitrary<Action> = fc.oneof(
  fc
    .constantFrom(...items("history"))
    .map((item) => ({ kind: "ask", item }) as Action),
  fc
    .constantFrom(...items("exam"))
    .map((item) => ({ kind: "examine", item }) as Action),
  fc
    .constantFrom(...items("test"))
    .map((item) => ({ kind: "order", item }) as Action),
  fc
    .constantFrom(...items("referral"))
    .map((item) => ({ kind: "refer", item }) as Action),
  fc
    .option(fc.integer({ min: 1, max: 3000 }), { nil: undefined })
    .map(
      (minutes) =>
        (minutes === undefined
          ? { kind: "wait" }
          : { kind: "wait", minutes }) as Action,
    ),
);

/** Applies the actions the engine accepts and skips the ones it refuses, as the server does. */
function playAccepted(actions: readonly Action[]): {
  state: EncounterState;
  accepted: Action[];
} {
  let state = initialState(pilot(), settings, "standard");
  const accepted: Action[] = [];
  for (const action of actions) {
    const result = applyAction(pilot(), settings, state, action);
    if (result.ok) {
      state = result.state;
      accepted.push(action);
    }
  }
  return { state, accepted };
}

const blocked = new Set(
  pilot()
    .bundle.facts.filter(
      (f) => f.release === "never" || f.release.startsWith("service."),
    )
    .map((f) => f.id),
);

describe("properties over random action sequences", () => {
  it("replay of the accepted actions is identical, and nothing is released early or out of bounds", () => {
    fc.assert(
      fc.property(fc.array(anyAction, { maxLength: 25 }), (actions) => {
        const { state, accepted } = playAccepted(actions);
        expect(replay(pilot(), settings, "standard", accepted)).toEqual(state);
        expect(state.releases.every((r) => r.at <= state.clock)).toBe(true);
        expect(state.pending.every((p) => p.dueAt > state.clock)).toBe(true);
        expect(state.releases.some((r) => blocked.has(r.source.id))).toBe(
          false,
        );
        expect(state.spend).toBeLessThanOrEqual(state.limits.budget);
        expect(state.clock).toBeLessThanOrEqual(
          settings.clock.max_stay_minutes,
        );
      }),
      { numRuns: 150, seed: 20260926 },
    );
  });

  it("a history answer is released only by a question that names it", () => {
    fc.assert(
      fc.property(fc.array(anyAction, { maxLength: 15 }), (actions) => {
        const { state } = playAccepted(actions);
        for (const release of state.releases) {
          if (release.source.table !== "fact" || release.via === null) continue;
          const fact = pilot().facts.get(release.source.id);
          const releasedByQuestion =
            fact?.released_by?.includes(release.via) ?? false;
          const releasedByTest =
            fact?.catalogue_ref?.startsWith("CMP.") ?? false;
          expect(releasedByQuestion || releasedByTest).toBe(true);
        }
      }),
      { numRuns: 100, seed: 7 },
    );
  });
});
