import { describe, expect, it } from "vitest";
import { buildDebrief, replay, type Action } from "../src/index.ts";
import { pilot, readConformance, scoring, settings } from "./helpers.ts";

const benchmark = (
  readConformance("PMC12949993/benchmark-path.json") as { actions: Action[] }
).actions;
const commitAction: Action = {
  kind: "commit",
  dx: "DX.LEAD_POISONING",
  evidence: ["H10", "L26"],
  plan: [
    "ACT.STOP_SUSPECTED_SOURCE",
    "RX.CHELATION.SUCCIMER_ORAL",
    "ACT.NOTIFY_PUBLIC_HEALTH",
    "ACT.REPEAT_BLOOD_LEAD",
  ],
};
const state = replay(pilot(), settings, "standard", [
  ...benchmark,
  commitAction,
]);
const debrief = buildDebrief(pilot(), settings, scoring, state);

describe("the debrief", () => {
  it("names the true diagnosis and carries the score", () => {
    expect(debrief.finalDiagnosis).toEqual({
      id: "DX.LEAD_POISONING",
      name: expect.any(String),
    });
    expect(debrief.score.diagnosis.anchor).toBe(5);
  });

  it("reveals the origin of every released item", () => {
    const origins = new Map(debrief.origins.map((o) => [o.id, o.origin]));
    expect(origins.get("H10")).toBe("article");
    expect(origins.get("S01.d0")).toBe("article");
    expect([...origins.values()]).toContain("normal");
    expect(debrief.origins).toHaveLength(
      state.releases.filter((r) => r.source.table !== "none").length,
    );
  });

  it("shows the provisional and final reports side by side", () => {
    expect(debrief.reports).toEqual([
      { test: "LAB.HAEM.FILM", provisional: "RP01", final: "RP02" },
    ]);
  });

  it("compares the player's path with the efficient path", () => {
    expect(debrief.paths.matched).toContain("LAB.TOX.BLOOD_LEAD");
    expect(debrief.paths.missed).toContain("LAB.TOX.ZPP");
    expect(debrief.paths.player.length).toBeGreaterThan(0);
    expect(debrief.paths.efficientCost).toBe(pilot().efficientPathCost);
    expect(debrief.paths.spend).toBe(state.spend);
  });

  it("lists every must-do with whether it was met, and the violations", () => {
    expect(debrief.mustDo.every((m) => m.met)).toBe(true);
    expect(debrief.mustNotDo).toEqual([]);
  });

  it("carries the figures of released reports and the attribution", () => {
    expect(debrief.figures.map((f) => f.id)).toEqual(
      expect.arrayContaining(["M01"]),
    );
    expect(debrief.attribution?.licence).toBe("CC BY 4.0");
    expect(debrief.keyDiscriminators.length).toBeGreaterThan(0);
  });

  it("is refused before a commit", () => {
    const open = replay(pilot(), settings, "standard", benchmark);
    expect(() => buildDebrief(pilot(), settings, scoring, open)).toThrow(
      /not been committed/,
    );
  });
});
