import { describe, expect, it } from "vitest";

import { conditionItems, diagnosisLabel, parseRubric, prettyJson } from "@/lib/ground-truth";

describe("parseRubric", () => {
  it("reads anchors with conditions and the default score", () => {
    const rubric = parseRubric({
      rubric: [{ score: 5, text: "Lead poisoning", if: { dx_in: ["DX.LEAD_POISONING"] } }],
      default_score: 1,
    });
    expect(rubric).toEqual({
      anchors: [{ score: 5, text: "Lead poisoning", condition: { dx_in: ["DX.LEAD_POISONING"] } }],
      defaultScore: 1,
      unparsed: null,
    });
  });

  it("reads a bare list of anchors", () => {
    expect(parseRubric([{ score: 2, text: "Partial" }, "Loose text"]).anchors).toEqual([
      { score: 2, text: "Partial", condition: null },
      { score: null, text: "Loose text", condition: null },
    ]);
  });

  it("keeps an unexpected shape as raw JSON", () => {
    expect(parseRubric({ something: "else" }).unparsed).toEqual({ something: "else" });
    expect(parseRubric(null)).toEqual({ anchors: [], defaultScore: null, unparsed: null });
  });
});

describe("conditionItems", () => {
  it("reads { text, if } items and plain strings", () => {
    expect(conditionItems([{ text: "Measure blood lead", if: { ordered_any: ["LAB.BLOOD_LEAD"] } }, "Stop the source"])).toEqual([
      { text: "Measure blood lead", condition: { ordered_any: ["LAB.BLOOD_LEAD"] } },
      { text: "Stop the source", condition: null },
    ]);
  });

  it("returns nothing for a non-list", () => {
    expect(conditionItems(null)).toEqual([]);
    expect(conditionItems({ text: "x" })).toEqual([]);
  });
});

describe("diagnosisLabel", () => {
  it("reads { id, text }", () => {
    expect(diagnosisLabel({ id: "DX.LEAD_POISONING", text: "Lead poisoning" })).toEqual({
      id: "DX.LEAD_POISONING",
      text: "Lead poisoning",
    });
  });

  it("reads a string or nothing", () => {
    expect(diagnosisLabel("Anaemia")).toEqual({ id: null, text: "Anaemia" });
    expect(diagnosisLabel(null)).toEqual({ id: null, text: "—" });
  });
});

describe("prettyJson", () => {
  it("indents by two spaces", () => {
    expect(prettyJson({ a: [1] })).toBe('{\n  "a": [\n    1\n  ]\n}');
  });
});
