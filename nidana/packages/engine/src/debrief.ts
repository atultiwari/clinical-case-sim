import type { Media } from "@nidana/contracts";
import type { Commit } from "./commit.ts";
import type { EncounterState, Release } from "./encounter.ts";
import { EngineError } from "./errors.ts";
import { groundTruthOf } from "./ground-truth.ts";
import type { PreparedCase } from "./prepare.ts";
import { scoreEncounter, type RuleOutcome, type Score } from "./scoring.ts";
import type { ScoringSettings } from "./scoring-settings.ts";
import type { Difficulty, DifficultySettings } from "./settings.ts";

/**
 * The debrief (SPEC §5.13): only after a commit, and the only place origins, the ground truth
 * and the source are revealed (invariant I4). Server-side; the server decides what to send.
 */

export interface ReleasedOrigin {
  readonly id: string;
  readonly table: Release["source"]["table"];
  /** `article`, `derived`, `affected`, `normal`, `rule` or `reviewer`; a report joins its origins with "+". */
  readonly origin: string;
}

export interface ReportPair {
  readonly test: string;
  readonly provisional: string;
  readonly final: string | null;
}

export interface Debrief {
  readonly bundleId: string;
  readonly difficulty: Difficulty;
  readonly finalDiagnosis: { readonly id: string; readonly name: string };
  readonly commit: Commit;
  readonly score: Score;
  readonly mustDo: readonly RuleOutcome[];
  readonly mustNotDo: readonly { readonly text: string }[];
  readonly paths: {
    readonly player: readonly string[];
    readonly efficient: readonly string[];
    readonly matched: readonly string[];
    readonly missed: readonly string[];
    readonly extra: readonly string[];
    readonly spend: number;
    readonly efficientCost: number;
    readonly committedAt: number;
  };
  readonly origins: readonly ReleasedOrigin[];
  readonly reports: readonly ReportPair[];
  readonly figures: readonly Media[];
  readonly differential: EncounterState["differential"];
  readonly keyDiscriminators: readonly string[];
  readonly teachingPoints: readonly string[];
  readonly acceptedDifferential: readonly string[];
  readonly redHerrings: readonly string[];
  readonly attribution: {
    readonly citation: string | null;
    readonly doi: string | null;
    readonly url: string | null;
    readonly licence: string;
    readonly attribution: string | null;
  } | null;
}

const strings = (value: unknown): string[] =>
  Array.isArray(value)
    ? value.filter((v): v is string => typeof v === "string")
    : [];

function originOf(prepared: PreparedCase, release: Release): string {
  const { table, id } = release.source;
  if (table === "fact") return prepared.facts.get(id)?.origin ?? "unknown";
  if (table === "ledger") return prepared.ledgerById.get(id)?.tier ?? "unknown";
  if (table === "report")
    return (prepared.reports.get(id)?.origins ?? []).join("+") || "unknown";
  return (
    prepared.bundle.consult_notes.find((n) => n.id === id)?.origin ?? "unknown"
  );
}

/** Items in the order the player first acted on them. */
function playerPath(state: EncounterState): string[] {
  const touched = [
    ...state.releases,
    ...state.pending.flatMap((p) => p.releases),
  ]
    .filter((r) => r.actionIndex >= 0 && r.via !== null)
    .sort((a, b) => a.actionIndex - b.actionIndex);
  return [...new Set(touched.map((r) => r.via as string))];
}

function reportPairs(
  prepared: PreparedCase,
  state: EncounterState,
): ReportPair[] {
  const ordered = new Set(state.ordered.map((o) => o.item));
  return prepared.bundle.reports
    .filter(
      (r) =>
        r.variant === "original" &&
        r.test_item_id != null &&
        ordered.has(r.test_item_id),
    )
    .map((r) => ({
      test: r.test_item_id as string,
      provisional: r.id,
      final: prepared.finalFor.get(r.id)?.id ?? null,
    }));
}

function figures(prepared: PreparedCase, state: EncounterState): Media[] {
  const reports = state.releases.filter((r) => r.source.table === "report");
  const rawIds = new Set(
    reports.flatMap((r) => prepared.reports.get(r.source.id)?.based_on ?? []),
  );
  const mediaIds = new Set(
    prepared.bundle.raw_material
      .filter((raw) => rawIds.has(raw.id))
      .flatMap((raw) => raw.media ?? []),
  );
  return prepared.bundle.media.filter((m) => mediaIds.has(m.id));
}

export function buildDebrief(
  prepared: PreparedCase,
  settings: DifficultySettings,
  scoring: ScoringSettings,
  state: EncounterState,
): Debrief {
  const commit = state.commit;
  if (commit === null)
    throw new EngineError(
      "not_committed",
      "The encounter has not been committed yet",
    );
  const score = scoreEncounter(prepared, settings, scoring, state);
  const truth = groundTruthOf(prepared);
  const { bundle } = prepared;
  const efficient =
    bundle.path_analysis.find((p) => p.kind === "efficient")?.items ?? [];
  const player = playerPath(state);
  const source = bundle.source;

  return {
    bundleId: bundle.bundle_id,
    difficulty: state.difficulty,
    finalDiagnosis: {
      id: truth.finalDx,
      name: prepared.items.get(truth.finalDx)?.name ?? truth.finalDx,
    },
    commit,
    score,
    mustDo: score.mustDo,
    mustNotDo: score.safety.violations,
    paths: {
      player,
      efficient,
      matched: efficient.filter((id) => player.includes(id)),
      missed: efficient.filter((id) => !player.includes(id)),
      extra: player.filter((id) => !efficient.includes(id)),
      spend: state.spend,
      efficientCost: prepared.efficientPathCost,
      committedAt: commit.at,
    },
    origins: state.releases
      .filter((r) => r.source.table !== "none")
      .map((r) => ({
        id: r.source.id,
        table: r.source.table,
        origin: originOf(prepared, r),
      })),
    reports: reportPairs(prepared, state),
    figures: figures(prepared, state),
    differential: state.differential,
    keyDiscriminators: strings(bundle.ground_truth.key_discriminators),
    teachingPoints: strings(bundle.ground_truth.teaching_points),
    acceptedDifferential: strings(bundle.ground_truth.accepted_differential),
    redHerrings: strings(bundle.ground_truth.red_herrings),
    attribution:
      source === null
        ? null
        : {
            citation: source.citation ?? null,
            doi: source.doi ?? null,
            url: source.url ?? null,
            licence: source.licence,
            attribution: source.attribution ?? null,
          },
  };
}
