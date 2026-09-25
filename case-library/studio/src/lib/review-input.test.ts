import { describe, expect, it } from "vitest";

import { decisionsFor, indexDecisions, type RowDecision } from "@/lib/decision-index";
import {
  isMaskedPath,
  parseEditedValue,
  parseFigureDecision,
  parseReviewDecision,
  reviewTargetId,
  studioBatchId,
} from "@/lib/review-input";

const CV = "PMC12949993@v1";
const LEDGER_ID = "0b7c2d4e-1f2a-4b3c-8d9e-0f1a2b3c4d5e";

function form(values: Record<string, string>) {
  return new Map(Object.entries(values));
}

describe("parseReviewDecision", () => {
  it("accepts an approval of a ledger row", () => {
    expect(
      parseReviewDecision(form({ caseVersionId: CV, targetTable: "synthetic_ledger", rowId: LEDGER_ID, decision: "approve" })),
    ).toEqual({
      ok: true,
      value: { caseVersionId: CV, targetTable: "synthetic_ledger", rowId: LEDGER_ID, decision: "approve", edited: null, note: null },
    });
  });

  it("parses an edit's new value as JSON, or keeps it as text", () => {
    const edit = (edited: string) =>
      parseReviewDecision(form({ caseVersionId: CV, targetTable: "fact", rowId: "H01", decision: "edit", edited, note: " n " }));
    expect(edit('{"value": 80}')).toMatchObject({ ok: true, value: { edited: { value: 80 }, note: "n" } });
    expect(edit("80")).toMatchObject({ ok: true, value: { edited: 80 } });
    expect(edit("Mild pallor")).toMatchObject({ ok: true, value: { edited: "Mild pallor" } });
  });

  it("drops a new value sent with approve or reject", () => {
    expect(
      parseReviewDecision(form({ caseVersionId: CV, targetTable: "report", rowId: "R01", decision: "reject", edited: "x" })),
    ).toMatchObject({ ok: true, value: { edited: null } });
  });

  it.each([
    [{ caseVersionId: "PMC1", targetTable: "fact", rowId: "H01", decision: "approve" }, /case version/],
    [{ caseVersionId: `${CV}'; drop table x;--`, targetTable: "fact", rowId: "H01", decision: "approve" }, /case version/],
    [{ caseVersionId: CV, targetTable: "ground_truth", rowId: "H01", decision: "approve" }, /kind of row/],
    [{ caseVersionId: CV, targetTable: "casevault.fact", rowId: "H01", decision: "approve" }, /kind of row/],
    [{ caseVersionId: CV, targetTable: "synthetic_ledger", rowId: "H01", decision: "approve" }, /Unknown row/],
    [{ caseVersionId: CV, targetTable: "fact", rowId: "../H01", decision: "approve" }, /Unknown row/],
    [{ caseVersionId: CV, targetTable: "fact", rowId: "", decision: "approve" }, /Unknown row/],
    [{ caseVersionId: CV, targetTable: "fact", rowId: "H01", decision: "ok" }, /approve, edit or reject/],
    [{ caseVersionId: CV, targetTable: "fact", rowId: "H01", decision: "APPROVE" }, /approve, edit or reject/],
    [{ caseVersionId: CV, targetTable: "fact", rowId: "H01", decision: "edit", edited: "  " }, /new value/],
    [{ caseVersionId: CV, targetTable: "fact", rowId: "H01", decision: "edit", edited: "x".repeat(4001) }, /longer/],
    [{ caseVersionId: CV, targetTable: "fact", rowId: "H01", decision: "approve", note: "x".repeat(1001) }, /longer/],
  ])("refuses %j", (values, error) => {
    const result = parseReviewDecision(form(values));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(error);
  });

  it("refuses a missing field and a non-text value", () => {
    expect(parseReviewDecision(form({ targetTable: "fact", rowId: "H01", decision: "approve" })).ok).toBe(false);
    const withFile = new Map<string, unknown>([
      ["caseVersionId", CV],
      ["targetTable", "fact"],
      ["rowId", new Blob(["H01"])],
      ["decision", "approve"],
    ]);
    expect(parseReviewDecision(withFile).ok).toBe(false);
  });
});

describe("parseFigureDecision", () => {
  it("accepts use and exclude without a path, and ignores a path sent with them", () => {
    expect(parseFigureDecision(form({ caseVersionId: CV, mediaId: "M01", decision: "use", maskedPath: "x" }))).toEqual({
      ok: true,
      value: { caseVersionId: CV, mediaId: "M01", decision: "use", maskedPath: null },
    });
    expect(parseFigureDecision(form({ caseVersionId: CV, mediaId: "M01", decision: "exclude" }))).toMatchObject({ ok: true });
  });

  it("accepts mask with a masked copy beside the figure", () => {
    expect(
      parseFigureDecision(form({ caseVersionId: CV, mediaId: "M01", decision: "mask", maskedPath: "PMC12949993/M01-masked.png" })),
    ).toMatchObject({ ok: true, value: { maskedPath: "PMC12949993/M01-masked.png" } });
  });

  it.each([
    [{ caseVersionId: CV, mediaId: "M01", decision: "pending" }, /use, mask or exclude/],
    [{ caseVersionId: CV, mediaId: "M/01", decision: "use" }, /Unknown figure/],
    [{ caseVersionId: "x", mediaId: "M01", decision: "use" }, /case version/],
    [{ caseVersionId: CV, mediaId: "M01", decision: "mask" }, /masked copy/],
    [{ caseVersionId: CV, mediaId: "M01", decision: "mask", maskedPath: "PMC999/M01.png" }, /masked copy/],
  ])("refuses %j", (values, error) => {
    const result = parseFigureDecision(form(values));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toMatch(error);
  });
});

describe("isMaskedPath", () => {
  it.each([
    ["PMC12949993/M01-masked.png", true],
    ["PMC12949993/fig1.masked.JPG", true],
    ["PMC12949993/M01.webp", true],
    ["PMC12949993/../PMC1/M01.png", false],
    ["PMC12949993/sub/M01.png", false],
    ["PMC12949993/M01.svg", false],
    ["PMC12949993/.hidden.png", false],
    ["PMC12949993/M01..png", false],
    ["PMC1294999/M01.png", false],
    ["/PMC12949993/M01.png", false],
    ["PMC12949993/M01.png?x=1", false],
    ["PMC12949993/M 01.png", false],
    [`PMC12949993/${"a".repeat(130)}.png`, false],
  ])("%s → %s", (path, expected) => {
    expect(isMaskedPath(CV, path)).toBe(expected);
  });
});

describe("ids", () => {
  it("builds review target ids", () => {
    expect(reviewTargetId("synthetic_ledger", CV, LEDGER_ID)).toBe(LEDGER_ID);
    expect(reviewTargetId("fact", CV, "H01")).toBe(`${CV}/H01`);
  });

  it("names Studio batches by UTC day and username", () => {
    const day = new Date("2026-09-26T23:30:00Z");
    expect(studioBatchId(day, "atul")).toBe("studio-2026-09-26-atul");
    expect(studioBatchId(day, "atul", 2)).toBe("studio-2026-09-26-atul-2");
  });

  it("keeps unparseable edits as text", () => {
    expect(parseEditedValue("{oops")).toBe("{oops");
  });
});

describe("decision index", () => {
  const row = (id: string, table: string, target: string): RowDecision => ({
    id,
    batch_id: "b",
    target_table: table,
    target_id: target,
    decision: "approve",
    edited: null,
    note: null,
    decided_by: "atul",
    decided_at: new Date(0),
  });

  it("groups decisions by table and row, so a report and a fact with the same id stay apart", () => {
    const index = indexDecisions([row("1", "fact", `${CV}/X1`), row("2", "report", `${CV}/X1`), row("3", "fact", `${CV}/X1`)]);
    expect(decisionsFor(index, "fact", CV, "X1").map((d) => d.id)).toEqual(["1", "3"]);
    expect(decisionsFor(index, "report", CV, "X1").map((d) => d.id)).toEqual(["2"]);
    expect(decisionsFor(index, "consult_note", CV, "X1")).toEqual([]);
  });
});
