import { describe, expect, it } from "vitest";
import {
  releasedIds,
  replay,
  valueOf,
  type Action,
  type Difficulty,
  type EncounterState,
} from "../src/index.ts";
import { pilot, settings } from "./helpers.ts";

const DAY = 1440;

function play(
  actions: readonly Action[],
  difficulty: Difficulty = "standard",
): EncounterState {
  return replay(pilot(), settings, difficulty, actions);
}

const ask = (item: string): Action => ({ kind: "ask", item });
const order = (item: string): Action => ({ kind: "order", item });
const wait = (minutes?: number): Action =>
  minutes === undefined ? { kind: "wait" } : { kind: "wait", minutes };

describe("the pilot at the start", () => {
  it("shows the vignette facts and nothing else", () => {
    const state = play([]);
    expect([...releasedIds(state)].sort()).toEqual([
      "H01",
      "H02",
      "H05",
      "H06",
    ]);
    expect(state.clock).toBe(0);
    expect(state.spend).toBe(0);
  });
});

describe("hidden history (ANALYSIS §3)", () => {
  it("current medicines releases H03 and H04 and not H10", () => {
    const ids = releasedIds(play([ask("HX.MEDS.CURRENT")]));
    expect(ids).toContain("H03");
    expect(ids).toContain("H04");
    expect(ids).not.toContain("H10");
  });

  it("a toxin question releases H09 only", () => {
    const before = releasedIds(play([]));
    const after = releasedIds(play([ask("HX.EXPOSURE.TOXINS")]));
    expect([...after].filter((id) => !before.has(id))).toEqual(["H09"]);
  });

  it("the remedies question releases H10", () => {
    expect(releasedIds(play([ask("HX.MEDS.SUPPLEMENTS")]))).toContain("H10");
  });

  it("answers from the ledger when no fact is released by the question", () => {
    const state = play([ask("HX.EXPOSURE.OCCUPATION")]);
    const last = state.releases.at(-1);
    expect(last?.source.table).toBe("ledger");
    expect(last?.via).toBe("HX.EXPOSURE.OCCUPATION");
  });

  it("takes five minutes per question and ten per examination", () => {
    const state = play([
      ask("HX.GI.BLEEDING"),
      { kind: "examine", item: "EX.GEN.PALLOR" },
    ]);
    expect(state.clock).toBe(15);
    expect(state.releases.at(-1)?.at).toBe(15);
  });
});

describe("results by day", () => {
  it("a blood count ordered on day 0 shows Hb 72", () => {
    const state = play([order("LAB.HAEM.CBC"), wait()]);
    expect(valueOf(pilot(), state, "CMP.HB")?.value).toBe("72");
  });

  it("a blood count ordered on day 4 shows Hb 64", () => {
    const state = play([wait(4 * DAY), order("LAB.HAEM.CBC"), wait()]);
    const hb = valueOf(pilot(), state, "CMP.HB");
    expect(hb?.value).toBe("64");
    expect(hb?.release.day).toBe(4);
  });

  it("an order on a day with no value returns the latest earlier value, marked with its day", () => {
    const state = play([wait(3 * DAY), order("LAB.CHEM.FERRITIN"), wait()]);
    const ferritin = valueOf(pilot(), state, "CMP.FERRITIN");
    expect(ferritin?.release.requestedDay).toBe(3);
    expect(ferritin?.release.day).toBe(0);
  });

  it("a result is not visible before its turnaround", () => {
    const state = play([order("LAB.HAEM.CBC"), ask("HX.GI.BLEEDING")]);
    expect(valueOf(pilot(), state, "CMP.HB")).toBeUndefined();
    expect(state.pending.map((p) => p.item)).toEqual(["LAB.HAEM.CBC"]);
    expect(state.pending[0]?.dueAt).toBe(240);
  });
});

describe("the blood lead", () => {
  it("appears only after its turnaround, at 77.8 µg/dL", () => {
    const early = play([order("LAB.TOX.BLOOD_LEAD"), wait(1439)]);
    expect(releasedIds(early)).not.toContain("L26");
    const due = play([order("LAB.TOX.BLOOD_LEAD"), wait()]);
    expect(due.clock).toBe(1440);
    expect(releasedIds(due)).toContain("L26");
    expect(valueOf(pilot(), due, "CMP.PB_BLOOD")?.value).toMatch(/^77\.8 /);
  });
});

describe("provisional and final film reports (N-014)", () => {
  it("Standard gives the provisional film report with its status line", () => {
    const state = play([order("LAB.HAEM.FILM"), wait()]);
    const report = state.releases.find((r) => r.source.table === "report");
    expect(report?.source.id).toBe("RP01");
    const rp01 = pilot().reports.get("RP01");
    expect(rp01?.status).toBe("provisional");
    expect(rp01?.status_line).toMatch(/^Provisional report/);
  });

  it("the film review gives the final report", () => {
    const state = play([
      order("LAB.HAEM.FILM"),
      order("LAB.HAEM.FILM_REVIEW"),
      wait(),
    ]);
    const reports = state.releases.filter((r) => r.source.table === "report");
    expect(reports.map((r) => r.source.id)).toEqual(["RP01", "RP02"]);
    expect(pilot().reports.get("RP02")?.status).toBe("final");
  });

  it("Guided mode gives the final report first", () => {
    const state = play([order("LAB.HAEM.FILM"), wait()], "guided");
    const reports = state.releases.filter((r) => r.source.table === "report");
    expect(reports.map((r) => [r.source.id, r.via])).toEqual([
      ["RP02", "LAB.HAEM.FILM"],
    ]);
  });

  it("Expert mode behaves as Standard", () => {
    const state = play([order("LAB.HAEM.FILM"), wait()], "expert");
    expect(
      state.releases.find((r) => r.source.table === "report")?.source.id,
    ).toBe("RP01");
  });
});

describe("referrals", () => {
  it("returns the consult note that matches the Chart at the moment of referral", () => {
    const before = play([{ kind: "refer", item: "REF.TOXICOLOGY" }, wait()]);
    expect(before.clock).toBe(240);
    expect(releasedIds(before)).toContain("CN04");

    const after = play([
      order("LAB.TOX.BLOOD_LEAD"),
      wait(),
      { kind: "refer", item: "REF.TOXICOLOGY" },
      wait(),
    ]);
    expect(releasedIds(after)).toContain("CN05");
    expect(releasedIds(after)).not.toContain("CN04");
  });

  it("uses finding conditions: stippling in the Chart gives the second haematology note", () => {
    const state = play([
      order("LAB.HAEM.FILM_REVIEW"),
      wait(),
      { kind: "refer", item: "REF.HAEMATOLOGY" },
      wait(),
    ]);
    expect(releasedIds(state)).toContain("CN02");
  });

  it("answers from the ledger for a specialty without consult notes", () => {
    const state = play([{ kind: "refer", item: "REF.DENTISTRY" }, wait()]);
    expect(state.releases.at(-1)?.source.table).toBe("ledger");
  });
});

describe("costs and determinism", () => {
  const path: Action[] = [
    ask("HX.MEDS.CURRENT"),
    order("LAB.HAEM.CBC"),
    order("LAB.HAEM.FILM"),
    order("LAB.TBS.DAT"),
    wait(),
    ask("HX.MEDS.SUPPLEMENTS"),
    order("LAB.HAEM.FILM_REVIEW"),
    order("LAB.TOX.BLOOD_LEAD"),
    { kind: "refer", item: "REF.TOXICOLOGY" },
    wait(),
    wait(),
  ];

  it("adds up the catalogue prices of every order", () => {
    const prices = new Map(
      pilot().catalogue.tests.map((t) => [t.item_id, t.price_inr ?? 0]),
    );
    const expected = path
      .filter((a) => a.kind === "order")
      .reduce((sum, a) => sum + (prices.get(a.item) ?? 0), 0);
    expect(play(path).spend).toBe(expected);
  });

  it("gives an identical state for the same actions", () => {
    expect(play(path)).toEqual(play([...path]));
  });

  it("releases the final film report and the blood lead on the benchmark path", () => {
    const state = play(path);
    expect(releasedIds(state)).toContain("L26");
    expect(releasedIds(state)).toContain("RP02");
  });
});
