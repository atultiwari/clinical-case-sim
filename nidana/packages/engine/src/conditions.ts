import type { Condition } from "@nidana/contracts";

/**
 * The condition vocabulary of Case Library SPEC §10.4, over what the engine knows exactly.
 * Commit conditions (`dx_in`, `evidence_has`, `plan_*`) are false until there is a commit.
 */

export interface ReleasedFinding {
  readonly finding: string;
  /** The test that was ordered and the report's own test. */
  readonly tests: ReadonlySet<string>;
}

export interface CommitFacts {
  readonly dx: string;
  readonly evidence: readonly string[];
  readonly plan: readonly string[];
}

export interface ConditionContext {
  /** Ids of released facts, ledger rows, reports and consult notes. */
  readonly released: ReadonlySet<string>;
  readonly findings: readonly ReleasedFinding[];
  readonly asked: ReadonlySet<string>;
  readonly ordered: ReadonlySet<string>;
  readonly referred: ReadonlySet<string>;
  readonly commit: CommitFacts | null;
}

/** An id ending in `.*` matches every item with that prefix. */
export function idMatches(pattern: string, id: string): boolean {
  return pattern.endsWith(".*")
    ? id.startsWith(pattern.slice(0, -1))
    : pattern === id;
}

const anyIn = (patterns: readonly string[], ids: Iterable<string>): boolean => {
  const list = [...ids];
  return patterns.some((p) => list.some((id) => idMatches(p, id)));
};

const allIn = (patterns: readonly string[], ids: Iterable<string>): boolean => {
  const list = [...ids];
  return patterns.every((p) => list.some((id) => idMatches(p, id)));
};

function firstIndex(pattern: string, plan: readonly string[]): number {
  return plan.findIndex((id) => idMatches(pattern, id));
}

function findingReleased(condition: Condition, ctx: ConditionContext): boolean {
  const spec = condition.finding_released;
  if (spec === undefined) return true;
  const findings = Array.isArray(spec) ? spec : spec.findings;
  const fromTests =
    (Array.isArray(spec) ? undefined : spec.from_tests) ?? condition.from_tests;
  return findings.every((finding) =>
    ctx.findings.some(
      (released) =>
        idMatches(finding, released.finding) &&
        (fromTests === undefined || anyIn(fromTests, released.tests)),
    ),
  );
}

type Check = (condition: Condition, ctx: ConditionContext) => boolean;

const CHECKS: Readonly<Record<string, Check>> = {
  released_any: (c, ctx) => anyIn(c.released_any ?? [], ctx.released),
  released_all: (c, ctx) => allIn(c.released_all ?? [], ctx.released),
  finding_released: findingReleased,
  // Read together with finding_released; on its own it adds nothing.
  from_tests: () => true,
  asked_any: (c, ctx) => anyIn(c.asked_any ?? [], ctx.asked),
  ordered_any: (c, ctx) => anyIn(c.ordered_any ?? [], ctx.ordered),
  ordered_all: (c, ctx) => allIn(c.ordered_all ?? [], ctx.ordered),
  referred_any: (c, ctx) => anyIn(c.referred_any ?? [], ctx.referred),
  dx_in: (c, ctx) =>
    ctx.commit !== null && anyIn(c.dx_in ?? [], [ctx.commit.dx]),
  evidence_has: (c, ctx) =>
    ctx.commit !== null && allIn(c.evidence_has ?? [], ctx.commit.evidence),
  plan_has: (c, ctx) =>
    ctx.commit !== null && allIn(c.plan_has ?? [], ctx.commit.plan),
  plan_has_any: (c, ctx) =>
    ctx.commit !== null && anyIn(c.plan_has_any ?? [], ctx.commit.plan),
  plan_before: (c, ctx) => {
    if (ctx.commit === null || c.plan_before === undefined) return false;
    const [first, second] = c.plan_before;
    const later = firstIndex(second, ctx.commit.plan);
    if (later < 0) return true;
    const earlier = firstIndex(first, ctx.commit.plan);
    return earlier >= 0 && earlier <= later;
  },
  not: (c, ctx) => c.not === undefined || !conditionHolds(c.not, ctx),
  all: (c, ctx) => (c.all ?? []).every((part) => conditionHolds(part, ctx)),
  any: (c, ctx) => (c.any ?? []).some((part) => conditionHolds(part, ctx)),
};

/** True when every keyword of the condition holds. A null condition always holds. */
export function conditionHolds(
  condition: Condition | null,
  ctx: ConditionContext,
): boolean {
  if (condition === null) return true;
  return Object.keys(condition).every((keyword) => {
    const check = CHECKS[keyword];
    if (check === undefined)
      throw new Error(`Unknown condition keyword "${keyword}"`);
    return check(condition, ctx);
  });
}
