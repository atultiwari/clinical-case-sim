import type {
  CaseBundle,
  CatalogueExport,
  CatalogueItem,
  CatalogueTest,
  ConsultNote,
  Fact,
  LedgerRow,
  Report,
} from "@nidana/contracts";
import { EngineError } from "./errors.ts";

/**
 * A bundle indexed for play, with the catalogue it was built on. Built once per bundle revision
 * and cached by the server; everything in it is read-only.
 */
export interface PreparedCase {
  readonly bundle: CaseBundle;
  readonly catalogue: CatalogueExport;
  readonly items: ReadonlyMap<string, CatalogueItem>;
  readonly tests: ReadonlyMap<string, CatalogueTest>;
  readonly facts: ReadonlyMap<string, Fact>;
  readonly reports: ReadonlyMap<string, Report>;
  /** Facts a player can see (release `vignette` or `chart`), by the question or examination that releases them. */
  readonly factsByItem: ReadonlyMap<string, readonly Fact[]>;
  /** Result facts a player can see, by component id. */
  readonly factsByComponent: ReadonlyMap<string, readonly Fact[]>;
  readonly ledgerById: ReadonlyMap<string, LedgerRow>;
  readonly ledgerByTarget: ReadonlyMap<string, readonly LedgerRow[]>;
  readonly reportsByTest: ReadonlyMap<string, readonly Report[]>;
  /** For each provisional (`original`) report, the final (`expert`) report on the same raw material. */
  readonly finalFor: ReadonlyMap<string, Report>;
  /** Consult notes by referral id, highest variant first. */
  readonly notesByReferral: ReadonlyMap<string, readonly ConsultNote[]>;
  readonly vignetteFacts: readonly Fact[];
  /** INR price of the tests on the efficient path, the basis of the budget. */
  readonly efficientPathCost: number;
}

const PLAYER_VISIBLE = new Set(["vignette", "chart"]);

function groupBy<T>(
  rows: readonly T[],
  keysOf: (row: T) => readonly string[],
): Map<string, T[]> {
  const groups = new Map<string, T[]>();
  for (const row of rows) {
    for (const key of keysOf(row))
      groups.set(key, [...(groups.get(key) ?? []), row]);
  }
  return groups;
}

function pairFinalReports(reports: readonly Report[]): Map<string, Report> {
  const experts = reports.filter((r) => r.variant === "expert");
  const pairs = new Map<string, Report>();
  for (const original of reports.filter((r) => r.variant === "original")) {
    const sources = new Set(original.based_on ?? []);
    const expert = experts.find((e) =>
      (e.based_on ?? []).some((id) => sources.has(id)),
    );
    if (expert !== undefined) pairs.set(original.id, expert);
  }
  return pairs;
}

function efficientPathCost(
  bundle: CaseBundle,
  tests: ReadonlyMap<string, CatalogueTest>,
): number {
  const efficient = [...bundle.path_analysis]
    .filter((path) => path.kind === "efficient")
    .sort((a, b) => a.path_id.localeCompare(b.path_id))[0];
  if (efficient === undefined) {
    throw new EngineError(
      "no_efficient_path",
      `${bundle.bundle_id} has no efficient path to set a budget from`,
    );
  }
  return efficient.items.reduce(
    (sum, item) => sum + (tests.get(item)?.price_inr ?? 0),
    0,
  );
}

export function prepareCase(
  bundle: CaseBundle,
  catalogue: CatalogueExport,
): PreparedCase {
  if (bundle.catalogue_version !== catalogue.version) {
    throw new EngineError(
      "catalogue_mismatch",
      `${bundle.bundle_id} was built on catalogue v${bundle.catalogue_version}, but the catalogue given is v${catalogue.version}`,
    );
  }
  const tests = new Map(catalogue.tests.map((t) => [t.item_id, t]));
  const visible = bundle.facts.filter((f) => PLAYER_VISIBLE.has(f.release));
  const notes = groupBy(bundle.consult_notes, (n) => [n.specialty]);
  return {
    bundle,
    catalogue,
    items: new Map(catalogue.items.map((i) => [i.id, i])),
    tests,
    facts: new Map(bundle.facts.map((f) => [f.id, f])),
    reports: new Map(bundle.reports.map((r) => [r.id, r])),
    factsByItem: groupBy(visible, (f) => f.released_by ?? []),
    factsByComponent: groupBy(
      visible.filter((f) => f.catalogue_ref?.startsWith("CMP.") ?? false),
      (f) => [f.catalogue_ref ?? ""],
    ),
    ledgerById: new Map(bundle.ledger.map((row) => [row.id, row])),
    ledgerByTarget: groupBy(bundle.ledger, (row) => [row.target]),
    reportsByTest: groupBy(bundle.reports, (r) =>
      r.test_item_id ? [r.test_item_id] : [],
    ),
    finalFor: pairFinalReports(bundle.reports),
    notesByReferral: new Map(
      [...notes].map(([referral, list]) => [
        referral,
        [...list].sort((a, b) => b.variant - a.variant),
      ]),
    ),
    vignetteFacts: bundle.facts.filter((f) => f.release === "vignette"),
    efficientPathCost: efficientPathCost(bundle, tests),
  };
}
