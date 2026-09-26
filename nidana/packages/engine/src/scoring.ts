import type { Commit } from "./commit.ts";
import { conditionHolds, type ConditionContext } from "./conditions.ts";
import type { EncounterState } from "./encounter.ts";
import { EngineError } from "./errors.ts";
import {
  groundTruthOf,
  type GroundTruth,
  type ScoredRule,
} from "./ground-truth.ts";
import type { PreparedCase } from "./prepare.ts";
import { conditionContext } from "./queries.ts";
import type { ScoringSettings } from "./scoring-settings.ts";
import type { DifficultySettings } from "./settings.ts";

/** Scoring (SPEC §7): deterministic, from the bundle's rules and the encounter (invariant I6). */

export interface RuleOutcome {
  readonly text: string;
  /** Null when the rule has no condition the engine can evaluate. */
  readonly met: boolean | null;
}

export interface Score {
  readonly version: string;
  readonly total: number;
  readonly diagnosis: {
    readonly anchor: number;
    readonly text: string | null;
    readonly points: number;
  };
  readonly management: {
    readonly points: number;
    readonly met: number;
    readonly scorable: number;
  };
  readonly mustDo: readonly RuleOutcome[];
  readonly efficiency: {
    readonly points: number;
    readonly cost: number;
    readonly tests: number;
    readonly time: number;
  };
  readonly reasoning: {
    readonly points: number;
    readonly differential: number;
    readonly discriminators: number;
    readonly referrals: number;
  };
  readonly safety: {
    readonly violations: readonly { readonly text: string }[];
    readonly penalty: number;
    readonly capApplied: boolean;
  };
}

interface Inputs {
  readonly prepared: PreparedCase;
  readonly settings: DifficultySettings;
  readonly scoring: ScoringSettings;
  readonly state: EncounterState;
  readonly commit: Commit;
  readonly truth: GroundTruth;
  readonly ctx: ConditionContext;
}

const holds = (rule: ScoredRule, ctx: ConditionContext): boolean | null =>
  rule.condition === null ? null : conditionHolds(rule.condition, ctx);

function diagnosis({ scoring, truth, ctx }: Inputs): Score["diagnosis"] {
  const anchor = truth.anchors.find((a) => conditionHolds(a.condition, ctx));
  const score = anchor?.score ?? truth.defaultAnchor;
  const points =
    scoring.diagnosis.points_by_anchor[
      String(score) as "1" | "2" | "3" | "4" | "5"
    ];
  return { anchor: score, text: anchor?.text ?? null, points };
}

function management({
  scoring,
  truth,
  ctx,
}: Inputs): Pick<Score, "management" | "mustDo"> {
  const mustDo = truth.mustDo.map((rule) => ({
    text: rule.text,
    met: holds(rule, ctx),
  }));
  const scorable = mustDo.filter((m) => m.met !== null).length;
  const met = mustDo.filter((m) => m.met === true).length;
  const share = scorable === 0 ? 1 : met / scorable;
  return {
    management: { points: scoring.management.points * share, met, scorable },
    mustDo,
  };
}

/** Minutes a strong player needs: the efficient path's questions and examinations, then its slowest test. */
function referenceMinutes(
  prepared: PreparedCase,
  settings: DifficultySettings,
): number {
  const efficient =
    prepared.bundle.path_analysis.find((p) => p.kind === "efficient")?.items ??
    [];
  const minutes = efficient.map((id) => {
    const kind = prepared.items.get(id)?.kind;
    if (kind === "history") return settings.clock.ask_minutes;
    if (kind === "exam") return settings.clock.examine_minutes;
    return 0;
  });
  const slowest = Math.max(
    0,
    ...efficient.map((id) => prepared.tests.get(id)?.tat_minutes ?? 0),
  );
  return minutes.reduce((a, b) => a + b, 0) + slowest;
}

function testPenalty({ prepared, scoring, state }: Inputs): number {
  const utility = new Map(
    prepared.bundle.test_utility.map((t) => [t.test_item_id, t.utility]),
  );
  const routine = new Set(scoring.efficiency.routine_tests);
  const penalties = [...new Set(state.ordered.map((o) => o.item))].map(
    (test) => {
      const rated =
        utility.get(test) ?? (routine.has(test) ? "supportive" : "unnecessary");
      if (rated === "risky") return scoring.efficiency.risky_test_penalty;
      return rated === "unnecessary"
        ? scoring.efficiency.unnecessary_test_penalty
        : 0;
    },
  );
  return penalties.reduce((a, b) => a + b, 0);
}

function efficiency(inputs: Inputs): Score["efficiency"] {
  const { prepared, settings, scoring, state, commit } = inputs;
  const { cost_points, test_points, time_points } = scoring.efficiency;
  const cost =
    state.spend <= prepared.efficientPathCost
      ? cost_points
      : (cost_points * prepared.efficientPathCost) / state.spend;
  const tests = Math.max(0, test_points - testPenalty(inputs));
  // Kept below the maximum stay, so the time marks always distinguish a quick commit from a slow one.
  const reference = Math.min(
    referenceMinutes(prepared, settings),
    state.limits.maxStayMinutes - 1,
  );
  const maxStay = state.limits.maxStayMinutes;
  const late =
    commit.at <= reference
      ? 1
      : Math.max(0, (maxStay - commit.at) / Math.max(1, maxStay - reference));
  const time = time_points * late;
  return { points: cost + tests + time, cost, tests, time };
}

function discriminatorShare({ prepared, state, ctx }: Inputs): number {
  const pivotal = prepared.bundle.facts
    .filter((f) => f.pivotal === true)
    .map((f) => f.id);
  const essential = prepared.bundle.test_utility
    .filter((t) => t.utility === "essential")
    .map((t) => t.test_item_id);
  const total = pivotal.length + essential.length;
  if (total === 0) return 1;
  const tested = new Set(state.releases.map((r) => r.via));
  const seen =
    pivotal.filter((id) => ctx.released.has(id)).length +
    essential.filter((id) => tested.has(id)).length;
  return seen / total;
}

function referralMarks({ prepared, scoring, state, commit }: Inputs): number {
  const onPaths = new Set(
    prepared.bundle.path_analysis.flatMap((p) => p.items),
  );
  const casework = new Set(
    prepared.bundle.consult_notes
      .filter((n) => n.origin === "affected")
      .map((n) => n.specialty),
  );
  const unjustified = [...new Set(state.referred)].filter(
    (ref) => !onPaths.has(ref) && !casework.has(ref),
  ).length;
  const efficient =
    prepared.bundle.path_analysis.find((p) => p.kind === "efficient")?.items ??
    [];
  const missed = efficient.filter(
    (id) =>
      id.startsWith("REF.") &&
      !state.referred.includes(id) &&
      !commit.plan.includes(id),
  ).length;
  const { referral_points, referral_penalty } = scoring.reasoning;
  return Math.max(
    0,
    referral_points - referral_penalty * (unjustified + missed),
  );
}

function reasoning(inputs: Inputs): Score["reasoning"] {
  const { scoring, state, truth } = inputs;
  const finalDifferential = state.differential.at(-1)?.items ?? [];
  const differential = finalDifferential.includes(truth.finalDx)
    ? scoring.reasoning.differential_points
    : 0;
  const discriminators =
    scoring.reasoning.discriminator_points * discriminatorShare(inputs);
  const referrals = referralMarks(inputs);
  return {
    points: differential + discriminators + referrals,
    differential,
    discriminators,
    referrals,
  };
}

/** Scores a committed encounter. */
export function scoreEncounter(
  prepared: PreparedCase,
  settings: DifficultySettings,
  scoring: ScoringSettings,
  state: EncounterState,
): Score {
  const commit = state.commit;
  if (commit === null)
    throw new EngineError(
      "not_committed",
      "The encounter has not been committed yet",
    );
  const truth = groundTruthOf(prepared);
  const ctx = conditionContext(prepared, state, commit);
  const inputs: Inputs = {
    prepared,
    settings,
    scoring,
    state,
    commit,
    truth,
    ctx,
  };

  const dx = diagnosis(inputs);
  const { management: mgmt, mustDo } = management(inputs);
  const eff = efficiency(inputs);
  const reason = reasoning(inputs);
  const violations = truth.mustNotDo
    .filter((rule) => holds(rule, ctx) === true)
    .map((rule) => ({ text: rule.text }));

  const raw = dx.points + mgmt.points + eff.points + reason.points;
  const penalty = scoring.safety.penalty_per_violation * violations.length;
  const capApplied = violations.length > 0;
  const penalised = raw - penalty;
  const total = Math.max(
    0,
    capApplied ? Math.min(penalised, scoring.safety.cap_total) : penalised,
  );

  return {
    version: scoring.version,
    total,
    diagnosis: dx,
    management: mgmt,
    mustDo,
    efficiency: eff,
    reasoning: reason,
    safety: { violations, penalty, capApplied },
  };
}
