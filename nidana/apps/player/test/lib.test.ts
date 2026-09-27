import type {
  ChartEntry,
  ResultValue,
  SearchItem,
} from "@nidana/contracts/api";
import { describe, expect, it } from "vitest";
import {
  blocksByDay,
  carriedLabel,
  chartBlocks,
  displayValue,
  trendOf,
} from "../src/lib/chart";
import {
  MAX_EVIDENCE,
  commitProblems,
  movePlanItem,
  toggleEvidence,
} from "../src/lib/commit";
import { formatClock, formatDuration, formatInr } from "../src/lib/format";
import { searchItems } from "../src/lib/search";

function entry(overrides: Partial<ChartEntry>): ChartEntry {
  return {
    ref: "c0",
    at: 0,
    kind: "result",
    item: "LAB.HAEM.CBC",
    itemName: "Full blood count",
    takenDay: null,
    requestedDay: 0,
    component: { id: "CMP.HB", name: "Haemoglobin" },
    text: null,
    value: {
      value: "72",
      unit: "g/L",
      refRange: "115-165",
      flag: "L",
      conventional: { unit: "g/dL", factor: 0.1, decimals: 1 },
    },
    report: null,
    recommendations: [],
    ...overrides,
  };
}

const HB: ResultValue = {
  value: "72",
  unit: "g/L",
  refRange: "115-165",
  flag: "L",
  conventional: { unit: "g/dL", factor: 0.1, decimals: 1 },
};

describe("format", () => {
  it("shows the simulated clock by day", () => {
    expect(formatClock(0)).toBe("Day 0, 00:00");
    expect(formatClock(285)).toBe("Day 0, 04:45");
    expect(formatClock(1735)).toBe("Day 1, 04:55");
  });

  it("shows durations and rupees", () => {
    expect(formatDuration(30)).toBe("30 min");
    expect(formatDuration(240)).toBe("4 h");
    expect(formatDuration(1440)).toBe("1 day");
    expect(formatDuration(3000)).toBe("2 days 2 h");
    expect(formatInr(20468)).toBe("₹20,468");
    expect(formatInr(123456)).toBe("₹1,23,456");
  });
});

describe("displayValue", () => {
  const value = HB;

  it("shows SI as stored and converts to conventional units, range included", () => {
    expect(displayValue(value, "si")).toEqual({
      text: "72",
      unit: "g/L",
      refRange: "115-165",
      flag: "L",
    });
    expect(displayValue(value, "conventional")).toEqual({
      text: "7.2",
      unit: "g/dL",
      refRange: "11.5–16.5",
      flag: "L",
    });
  });

  it("leaves text results and values without a conversion alone", () => {
    const text = { ...value, value: "Not detected" };
    expect(displayValue(text, "conventional").text).toBe("Not detected");
    const noConv = { ...value, conventional: null };
    expect(displayValue(noConv, "conventional").unit).toBe("g/L");
    const oddRange = { ...value, refRange: "<5" };
    expect(displayValue(oddRange, "conventional").refRange).toBeNull();
    const precise = {
      ...value,
      conventional: { unit: "x", factor: 1 / 3, decimals: null },
    };
    expect(displayValue(precise, "conventional").text).toBe("24");
  });
});

describe("chartBlocks", () => {
  it("groups one order's results into a table and keeps other entries apart", () => {
    const blocks = chartBlocks([
      entry({
        ref: "c0",
        kind: "history",
        component: null,
        value: null,
        text: "Tired",
        item: "HX.GEN.FATIGUE",
      }),
      entry({ ref: "c1", at: 240 }),
      entry({
        ref: "c2",
        at: 240,
        component: { id: "CMP.PLT", name: "Platelets" },
      }),
      entry({ ref: "c3", at: 480 }),
    ]);
    expect(blocks.map((b) => b.type)).toEqual(["entry", "results", "results"]);
    const first = blocks[1];
    expect(
      first?.type === "results" && first.table.rows.map((r) => r.name),
    ).toEqual(["Haemoglobin", "Platelets"]);
  });

  it("arranges blocks by day", () => {
    const days = blocksByDay([
      entry({ at: 10 }),
      entry({ at: 1500 }),
      entry({ at: 20, kind: "exam", component: null, value: null }),
    ]);
    expect(days.map((d) => d.day)).toEqual([0, 1]);
    expect(days[0]?.blocks).toHaveLength(2);
  });
});

describe("trendOf and carriedLabel", () => {
  it("builds one point per day, the latest release winning", () => {
    const points = trendOf(
      [
        entry({ requestedDay: 0, value: { ...HB, value: "72" } }),
        entry({ requestedDay: 4, value: { ...HB, value: "64" } }),
        entry({ requestedDay: 4, value: { ...HB, value: "65" } }),
        entry({
          requestedDay: 2,
          component: { id: "CMP.PLT", name: "Platelets" },
        }),
        entry({
          requestedDay: 3,
          value: { ...HB, value: "n/a" },
        }),
      ],
      "CMP.HB",
    );
    expect(points.map((p) => [p.day, p.value])).toEqual([
      [0, 72],
      [4, 65],
    ]);
  });

  it("labels a carried-forward value with the day it was taken", () => {
    expect(carriedLabel(entry({ takenDay: 0, requestedDay: 3 }))).toBe(
      "Result from day 0",
    );
    expect(carriedLabel(entry({}))).toBeNull();
  });
});

describe("searchItems", () => {
  const items: SearchItem[] = [
    {
      id: "HX.MEDS.SUPPLEMENTS",
      kind: "history",
      name: "Herbal, traditional or over-the-counter remedies",
      category: "",
      synonyms: ["supplements", "ayurvedic"],
    },
    {
      id: "HX.MEDS.CURRENT",
      kind: "history",
      name: "Current medicines",
      category: "",
      synonyms: ["drugs", "medications"],
    },
    {
      id: "LAB.HAEM.CBC",
      kind: "test",
      name: "Full blood count",
      category: "",
      synonyms: ["FBC", "CBC"],
      priceInr: 300,
      turnaroundMinutes: 240,
    },
    {
      id: "LAB.TOX.BLOOD_LEAD",
      kind: "test",
      name: "Blood lead",
      category: "",
      synonyms: ["lead level"],
    },
  ];

  it("finds items by name, word or synonym, only of the kinds asked for", () => {
    expect(
      searchItems(items, ["history"], "supplements").map((i) => i.id),
    ).toEqual(["HX.MEDS.SUPPLEMENTS"]);
    expect(searchItems(items, ["test"], "cbc").map((i) => i.id)).toEqual([
      "LAB.HAEM.CBC",
    ]);
    expect(searchItems(items, ["test"], "blood").map((i) => i.id)).toEqual([
      "LAB.TOX.BLOOD_LEAD",
      "LAB.HAEM.CBC",
    ]);
    expect(searchItems(items, ["history"], "cbc")).toEqual([]);
    expect(
      searchItems(items, ["history"], "Ayurvédic").map((i) => i.id),
    ).toEqual(["HX.MEDS.SUPPLEMENTS"]);
    expect(
      searchItems(items, ["history"], "over counter").map((i) => i.id),
    ).toEqual(["HX.MEDS.SUPPLEMENTS"]);
  });

  it("needs at least two characters and respects the limit", () => {
    expect(searchItems(items, ["test"], "b")).toEqual([]);
    expect(
      searchItems(items, ["history", "test"], "full blood count", 1),
    ).toHaveLength(1);
    expect(searchItems(items, ["test"], "Full blood count")[0]?.id).toBe(
      "LAB.HAEM.CBC",
    );
  });
});

describe("commit helpers", () => {
  it("lists what is missing or wrong", () => {
    expect(commitProblems({ dx: null, evidence: [], plan: [] })).toEqual([
      "Choose a final diagnosis.",
    ]);
    expect(
      commitProblems({
        dx: "DX.A",
        evidence: ["c1", "c2", "c3", "c4", "c5", "c6"],
        plan: ["A", "A"],
      }),
    ).toHaveLength(2);
    expect(
      commitProblems({ dx: "DX.A", evidence: ["c1"], plan: ["A"] }),
    ).toEqual([]);
  });

  it("toggles evidence up to the limit", () => {
    const full = Array.from({ length: MAX_EVIDENCE }, (_, i) => `c${i}`);
    expect(toggleEvidence(full, "c9")).toEqual(full);
    expect(toggleEvidence(full, "c0")).not.toContain("c0");
    expect(toggleEvidence([], "c1")).toEqual(["c1"]);
  });

  it("moves plan items within bounds", () => {
    expect(movePlanItem(["a", "b", "c"], 2, -1)).toEqual(["a", "c", "b"]);
    expect(movePlanItem(["a", "b"], 0, -1)).toEqual(["a", "b"]);
    expect(movePlanItem(["a", "b"], 5, 1)).toEqual(["a", "b"]);
  });
});

describe("nicknameProblem", () => {
  it("accepts a short nickname and refuses emails, symbols and odd lengths", async () => {
    const { nicknameProblem } = await import("../src/lib/account-rules");
    expect(nicknameProblem("Night owl")).toBeNull();
    expect(nicknameProblem("Ānanya_2")).toBeNull();
    expect(nicknameProblem("a")).toMatch(/2 to 24/);
    expect(nicknameProblem("x".repeat(25))).toMatch(/2 to 24/);
    expect(nicknameProblem("me@example.org")).toMatch(/letters/);
  });
});
