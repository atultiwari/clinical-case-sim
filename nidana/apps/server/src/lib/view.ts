import type { Fact, LedgerRow } from "@nidana/contracts";
import type {
  ChartEntry,
  EntryKind,
  PlayerView,
  ResultValue,
} from "@nidana/contracts";
import type { EncounterState, PreparedCase, Release } from "@nidana/engine";

/**
 * The PlayerView (SPEC §6.3): everything the app may show, and nothing else. It never holds
 * the bundle id (it names the source article), origins, row ids, finding ids, the ground
 * truth or anything not yet released (invariants I1 and I4). Chart entries get per-encounter
 * references (`c0`, `c1`, …) that the player cites as evidence; the server maps them back.
 */

export type {
  ChartEntry,
  EntryKind,
  PlayerView,
  ResultValue,
} from "@nidana/contracts";

const REF = /^c(\d+)$/;

export const refOf = (index: number): string => `c${index}`;

/** The source id a chart reference points to, if the reference is valid and released. */
export function sourceOfRef(state: EncounterState, ref: string): string | null {
  const index = Number(REF.exec(ref)?.[1] ?? Number.NaN);
  const release = Number.isInteger(index) ? state.releases[index] : undefined;
  return release === undefined || release.source.table === "none"
    ? null
    : release.source.id;
}

const KIND_BY_ITEM: Readonly<Record<string, EntryKind>> = {
  history: "history",
  exam: "exam",
  test: "result",
  referral: "consult",
};

const str = (value: unknown): string | null =>
  typeof value === "string"
    ? value
    : typeof value === "number"
      ? String(value)
      : null;

const componentIndex = new WeakMap<
  PreparedCase,
  Map<string, PreparedCase["catalogue"]["components"][number]>
>();

function componentDef(prepared: PreparedCase, id: string | null) {
  let index = componentIndex.get(prepared);
  if (index === undefined) {
    index = new Map(prepared.catalogue.components.map((c) => [c.id, c]));
    componentIndex.set(prepared, index);
  }
  return id === null ? undefined : index.get(id);
}

function conventionalOf(
  prepared: PreparedCase,
  component: string | null,
): ResultValue["conventional"] {
  const def = componentDef(prepared, component);
  if (def?.unit_conv == null || def.conv_factor == null) return null;
  return {
    unit: def.unit_conv,
    factor: def.conv_factor,
    decimals: def.decimals,
  };
}

function factEntry(
  prepared: PreparedCase,
  fact: Fact,
  kind: EntryKind,
  release: Release,
): Partial<ChartEntry> {
  if (kind === "result") {
    return {
      value: {
        value: fact.value ?? "",
        unit: fact.unit ?? null,
        refRange: fact.ref_range ?? null,
        flag: fact.flag ?? null,
        conventional: conventionalOf(prepared, release.component),
      },
    };
  }
  const words =
    kind === "history"
      ? (fact.lay_text ?? fact.release_text)
      : fact.release_text;
  return { text: words ?? fact.value ?? null };
}

function ledgerEntry(
  prepared: PreparedCase,
  row: LedgerRow,
  kind: EntryKind,
  release: Release,
): Partial<ChartEntry> {
  const stored = row.value;
  if (kind === "result" && stored.value !== undefined) {
    return {
      value: {
        value: str(stored.value) ?? "",
        unit: str(stored.unit),
        refRange: str(stored.ref_range),
        flag: str(stored.flag),
        conventional: conventionalOf(prepared, release.component),
      },
    };
  }
  const words =
    kind === "history" ? (row.lay_text ?? row.release_text) : row.release_text;
  return { text: words ?? str(stored.text) };
}

function contentOf(
  prepared: PreparedCase,
  release: Release,
  kind: EntryKind,
): Partial<ChartEntry> {
  const { table, id } = release.source;
  if (table === "fact") {
    const fact = prepared.facts.get(id);
    return fact === undefined ? {} : factEntry(prepared, fact, kind, release);
  }
  if (table === "ledger") {
    const row = prepared.ledgerById.get(id);
    return row === undefined ? {} : ledgerEntry(prepared, row, kind, release);
  }
  if (table === "report") {
    const report = prepared.reports.get(id);
    return report === undefined
      ? {}
      : {
          report: {
            status: report.status,
            statusLine: report.status_line ?? null,
            text: report.report_text ?? null,
            impression: report.impression ?? null,
            suggestedTests: report.suggested_reflex ?? [],
          },
        };
  }
  if (table === "consult_note") {
    const note = prepared.bundle.consult_notes.find((n) => n.id === id);
    return {
      text: note?.note_text ?? null,
      recommendations: note?.recommendations ?? [],
    };
  }
  return {};
}

function kindOf(prepared: PreparedCase, release: Release): EntryKind {
  if (release.source.table === "none") return "no_record";
  if (release.source.table === "report") return "report";
  if (release.via === null) return "vignette";
  return KIND_BY_ITEM[prepared.items.get(release.via)?.kind ?? ""] ?? "result";
}

function entryOf(
  prepared: PreparedCase,
  release: Release,
  index: number,
): ChartEntry {
  const kind = kindOf(prepared, release);
  const componentName = componentDef(prepared, release.component)?.name;
  const carried =
    release.day !== null &&
    release.requestedDay !== null &&
    release.day !== release.requestedDay;
  return {
    ref: refOf(index),
    at: release.at,
    kind,
    item: release.via,
    itemName:
      release.via === null
        ? null
        : (prepared.items.get(release.via)?.name ?? null),
    takenDay: carried ? release.day : null,
    requestedDay: release.requestedDay,
    component:
      release.component === null
        ? null
        : { id: release.component, name: componentName ?? release.component },
    text: null,
    value: null,
    report: null,
    recommendations: [],
    ...contentOf(prepared, release, kind),
  };
}

export function buildPlayerView(
  prepared: PreparedCase,
  state: EncounterState,
  encounterId: string,
): PlayerView {
  const card = prepared.bundle.case;
  return {
    encounterId,
    status: state.commit === null ? "active" : "committed",
    difficulty: state.difficulty,
    case: {
      slug: card.slug ?? "",
      title: card.display_title ?? "Untitled case",
      tags: card.display_tags ?? [],
      specialty: card.specialty ?? null,
      vignette: prepared.bundle.vignette,
      openingStatement: prepared.bundle.opening_statement_lay,
    },
    clock: state.clock,
    day: Math.floor(state.clock / 1440),
    spend: state.spend,
    limits: {
      budget: state.limits.budget,
      budgetLeft: state.limits.budget - state.spend,
      maxStayMinutes: state.limits.maxStayMinutes,
      referralsAllowed: state.limits.referralsAllowed,
      referralsUsed: state.referred.length,
    },
    mustCommit: state.mustCommit,
    chart: state.releases.map((release, index) =>
      entryOf(prepared, release, index),
    ),
    pending: state.pending.map((p) => ({
      item: p.item,
      itemName: prepared.items.get(p.item)?.name ?? null,
      kind: p.kind,
      orderedAt: p.orderedAt,
      dueAt: p.dueAt,
    })),
    differential: state.differential,
  };
}
