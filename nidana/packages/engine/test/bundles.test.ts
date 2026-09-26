import { describe, expect, it } from "vitest";
import {
  EngineError,
  prepareCase,
  replay,
  type Action,
  type DifficultySettings,
} from "../src/index.ts";
import {
  PILOT,
  catalogue,
  loadBundle,
  newestBundleNames,
  settings,
} from "./helpers.ts";

const ACTION_FOR_KIND: Readonly<Record<string, Action["kind"]>> = {
  history: "ask",
  exam: "examine",
  test: "order",
  referral: "refer",
};

/** No budget or referral limit, so every item can be tried on its own. */
const unlimited: DifficultySettings = {
  ...settings,
  difficulties: {
    ...settings.difficulties,
    guided: {
      ...settings.difficulties.guided,
      budget_factor: 1e9,
      referrals_allowed: 1e9,
    },
  },
};

describe("every exported bundle on the pinned catalogue", () => {
  const names = newestBundleNames();

  it("are the newest revision of every case, the pilot's included", () => {
    expect(names).toContain(PILOT);
    expect(
      names.every((name) => loadBundle(name).catalogue_version === 2),
    ).toBe(true);
  });

  it.each(names)("%s answers every item the Attending can use", (name) => {
    const prepared = prepareCase(loadBundle(name), catalogue);
    expect(prepared.efficientPathCost).toBeGreaterThan(0);
    const unanswered = catalogue.items
      .filter(
        (item) =>
          item.specialty_scope.includes("attending") &&
          item.kind in ACTION_FOR_KIND,
      )
      .filter((item) => {
        const action = {
          kind: ACTION_FOR_KIND[item.kind],
          item: item.id,
        } as Action;
        const state = replay(prepared, unlimited, "guided", [
          action,
          { kind: "wait", minutes: 10_000 },
        ]);
        return state.releases.some(
          (r) => r.via === item.id && r.source.table === "none",
        );
      })
      .map((item) => item.id);
    expect(unanswered).toEqual([]);
  });
});

describe("prepareCase", () => {
  it("refuses a bundle built on another catalogue version", () => {
    const old = loadBundle("PMC12949993@v1.r1");
    expect(() => prepareCase(old, catalogue)).toThrow(EngineError);
    expect(() => prepareCase(old, catalogue)).toThrow(/catalogue v1.*v2/);
  });

  it("refuses a bundle with no efficient path", () => {
    const bundle = { ...loadBundle(PILOT), path_analysis: [] };
    expect(() => prepareCase(bundle, catalogue)).toThrow(/no efficient path/);
  });
});

describe("parseDifficultySettings", () => {
  it("explains what is wrong with bad settings", async () => {
    const { parseDifficultySettings } = await import("../src/index.ts");
    expect(() =>
      parseDifficultySettings({
        ...settings,
        clock: { ...settings.clock, ask_minutes: 0 },
      }),
    ).toThrow(/ask_minutes/);
  });
});
