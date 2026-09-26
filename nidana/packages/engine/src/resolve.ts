import type { Fact, LedgerRow, Report } from "@nidana/contracts";
import { conditionHolds, type ConditionContext } from "./conditions.ts";
import type { PreparedCase } from "./prepare.ts";
import type { Level } from "./settings.ts";

/**
 * What an item releases on a given simulated day (SPEC §5.5 to §5.10). Only stored content is
 * released (invariant I2); `none` marks an item the bundle cannot answer, which full coverage
 * (Case Library invariant L2) should make impossible.
 */

export type SourceTable =
  "fact" | "ledger" | "report" | "consult_note" | "none";

export interface Source {
  readonly table: SourceTable;
  readonly id: string;
}

export interface ReleaseDraft {
  /** The catalogue item that released it; null for the vignette. */
  readonly via: string | null;
  readonly source: Source;
  /** The component a result belongs to. */
  readonly component: string | null;
  /** The day the value was taken; null means valid throughout the admission. */
  readonly day: number | null;
  /** The simulated day the item was asked for or ordered on. */
  readonly requestedDay: number | null;
}

interface Dated {
  readonly day: number | null;
  readonly source: Source;
}

const fromFact = (fact: Fact): Dated => ({
  day: fact.day,
  source: { table: "fact", id: fact.id },
});
const fromRow = (row: LedgerRow): Dated => ({
  day: row.day_bucket,
  source: { table: "ledger", id: row.id },
});

/**
 * The rows valid on `day`: those on the latest day at or before it, or, if there are none, the
 * rows valid throughout. Earlier rows in `rows` win ties, so facts listed first beat the ledger.
 */
function validOn(rows: readonly Dated[], day: number): Dated[] {
  const dated = rows.filter((r) => r.day !== null && r.day <= day);
  if (dated.length > 0) {
    const latest = Math.max(...dated.map((r) => r.day as number));
    return dated.filter((r) => r.day === latest);
  }
  return rows.filter((r) => r.day === null);
}

function draft(
  via: string,
  row: Dated,
  day: number,
  component: string | null = null,
): ReleaseDraft {
  return {
    via,
    source: row.source,
    component,
    day: row.day,
    requestedDay: day,
  };
}

function nothing(
  via: string,
  id: string,
  day: number,
  component: string | null = null,
): ReleaseDraft {
  return {
    via,
    source: { table: "none", id },
    component,
    day: null,
    requestedDay: day,
  };
}

/** A history question or an examination: its facts (undated ones and the latest dated ones) and its ledger answer. */
export function answerItem(
  prepared: PreparedCase,
  item: string,
  day: number,
): ReleaseDraft[] {
  const facts = (prepared.factsByItem.get(item) ?? []).map(fromFact);
  const undated = facts.filter((f) => f.day === null);
  const dated = validOn(
    facts.filter((f) => f.day !== null),
    day,
  );
  const ledger = validOn(
    (prepared.ledgerByTarget.get(item) ?? []).map(fromRow),
    day,
  ).slice(0, 1);
  const rows = [...undated, ...dated, ...ledger];
  return rows.length > 0
    ? rows.map((row) => draft(item, row, day))
    : [nothing(item, item, day)];
}

function componentValue(
  prepared: PreparedCase,
  test: string,
  component: string,
  day: number,
): ReleaseDraft {
  const rows = [
    ...(prepared.factsByComponent.get(component) ?? []).map(fromFact),
    ...(prepared.ledgerByTarget.get(component) ?? []).map(fromRow),
  ];
  const row = validOn(rows, day)[0];
  return row === undefined
    ? nothing(test, component, day, component)
    : draft(test, row, day, component);
}

function reportsFor(
  prepared: PreparedCase,
  test: string,
  level: Level,
): Report[] {
  const reports = (prepared.reportsByTest.get(test) ?? []).map((report) => {
    const final = prepared.finalFor.get(report.id);
    return level.first_report === "final" && final !== undefined
      ? final
      : report;
  });
  return reports.filter(
    (report, i) => reports.findIndex((r) => r.id === report.id) === i,
  );
}

/** A test: a test-level answer (such as "Not applicable"), else its report, else a value per component. */
export function resultsForTest(
  prepared: PreparedCase,
  test: string,
  day: number,
  level: Level,
): ReleaseDraft[] {
  const testRow = validOn(
    (prepared.ledgerByTarget.get(test) ?? []).map(fromRow),
    day,
  )[0];
  if (testRow !== undefined) return [draft(test, testRow, day)];

  const reports = reportsFor(prepared, test, level);
  if (reports.length > 0) {
    return reports.map((r) => ({
      via: test,
      source: { table: "report", id: r.id },
      component: null,
      day,
      requestedDay: day,
    }));
  }
  const components = prepared.tests.get(test)?.components ?? [];
  return components.map((component) =>
    componentValue(prepared, test, component, day),
  );
}

/** A referral: the highest consult note variant whose condition holds now, else the ledger's generic note. */
export function consultFor(
  prepared: PreparedCase,
  referral: string,
  day: number,
  ctx: ConditionContext,
): ReleaseDraft {
  const note = (prepared.notesByReferral.get(referral) ?? []).find((n) =>
    conditionHolds(n.condition ?? null, ctx),
  );
  if (note !== undefined) {
    return {
      via: referral,
      source: { table: "consult_note", id: note.id },
      component: null,
      day,
      requestedDay: day,
    };
  }
  const row = validOn(
    (prepared.ledgerByTarget.get(referral) ?? []).map(fromRow),
    day,
  )[0];
  return row === undefined
    ? nothing(referral, referral, day)
    : draft(referral, row, day);
}
