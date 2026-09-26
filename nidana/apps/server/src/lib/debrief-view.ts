import type { DebriefView, Origin, ReportContent } from "@nidana/contracts";
import type { Debrief, EncounterState, PreparedCase } from "@nidana/engine";
import { refOf } from "./view";

/**
 * The debrief as the app shows it (SPEC §5.13): Chart entries by their references, items by
 * name, and report texts, so the app can mark synthetic results and show the provisional and
 * final reports side by side. Only after the commit.
 */

const ORIGINS = new Set<Origin>([
  "article",
  "derived",
  "affected",
  "normal",
  "rule",
  "reviewer",
]);

function named(
  prepared: PreparedCase,
  id: string,
): { id: string; name: string } {
  return { id, name: prepared.items.get(id)?.name ?? id };
}

function reportContent(
  prepared: PreparedCase,
  id: string,
): ReportContent | null {
  const report = prepared.reports.get(id);
  return report === undefined
    ? null
    : {
        status: report.status,
        statusLine: report.status_line ?? null,
        text: report.report_text ?? null,
        impression: report.impression ?? null,
        suggestedTests: report.suggested_reflex ?? [],
      };
}

/** A report's origins are joined with "+"; the most synthetic one decides how it is marked. */
function originOf(raw: string): Origin {
  const parts = raw
    .split("+")
    .filter((p): p is Origin => ORIGINS.has(p as Origin));
  const order: Origin[] = [
    "affected",
    "reviewer",
    "rule",
    "normal",
    "derived",
    "article",
  ];
  return order.find((o) => parts.includes(o)) ?? "unknown";
}

export function buildDebriefView(
  prepared: PreparedCase,
  state: EncounterState,
  debrief: Debrief,
): DebriefView {
  const released = new Set(state.releases.map((r) => r.source.id));
  const origins: Record<string, Origin> = {};
  state.releases.forEach((release, index) => {
    if (release.source.table === "none") return;
    const found = debrief.origins.find(
      (o) => o.id === release.source.id && o.table === release.source.table,
    );
    origins[refOf(index)] =
      found === undefined ? "unknown" : originOf(found.origin);
  });
  const player = new Set(debrief.paths.player);
  const evidenceRefs = debrief.commit.evidence.map((id) => {
    const index = state.releases.findIndex((r) => r.source.id === id);
    return index < 0 ? id : refOf(index);
  });
  return {
    finalDiagnosis: debrief.finalDiagnosis,
    committed: {
      dx: named(prepared, debrief.commit.dx),
      evidence: evidenceRefs,
      plan: debrief.commit.plan.map((id) => named(prepared, id)),
      at: debrief.commit.at,
    },
    score: debrief.score,
    paths: {
      player: debrief.paths.player.map((id) => named(prepared, id)),
      // Components (CMP.*) are what tests measure, not things a player does; the path lists actions only.
      efficient: debrief.paths.efficient
        .filter((id) => prepared.items.has(id))
        .map((id) => ({ ...named(prepared, id), done: player.has(id) })),
      spend: debrief.paths.spend,
      efficientCost: debrief.paths.efficientCost,
    },
    origins,
    reports: debrief.reports.flatMap((pair) => {
      const provisional = reportContent(prepared, pair.provisional);
      if (provisional === null) return [];
      return [
        {
          test: pair.test,
          testName: named(prepared, pair.test).name,
          provisional,
          final:
            pair.final === null ? null : reportContent(prepared, pair.final),
          finalSeen: pair.final !== null && released.has(pair.final),
        },
      ];
    }),
    keyDiscriminators: debrief.keyDiscriminators,
    teachingPoints: debrief.teachingPoints,
    acceptedDifferential: debrief.acceptedDifferential,
    redHerrings: debrief.redHerrings,
    source: debrief.attribution,
  };
}
