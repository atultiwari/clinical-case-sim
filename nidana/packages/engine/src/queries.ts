import type {
  CommitFacts,
  ConditionContext,
  ReleasedFinding,
} from "./conditions.ts";
import type { EncounterState, Release } from "./encounter.ts";
import type { PreparedCase } from "./prepare.ts";

/** Read-only views of an encounter state. */

/** Ids of every fact, ledger row, report and consult note in the Chart. */
export function releasedIds(state: EncounterState): Set<string> {
  return new Set(
    state.releases
      .filter((r) => r.source.table !== "none")
      .map((r) => r.source.id),
  );
}

export interface ResultValue {
  /** The value as stored: a fact's value, or a ledger row's value or text. */
  readonly value: string;
  readonly release: Release;
}

/** The latest released value of a component, if any. */
export function valueOf(
  prepared: PreparedCase,
  state: EncounterState,
  component: string,
): ResultValue | undefined {
  const release = state.releases.findLast(
    (r) => r.component === component && r.source.table !== "none",
  );
  if (release === undefined) return undefined;
  if (release.source.table === "fact") {
    const value = prepared.facts.get(release.source.id)?.value;
    return value == null ? undefined : { value, release };
  }
  const row = prepared.bundle.ledger.find((l) => l.id === release.source.id);
  const stored = row?.value.value ?? row?.value.text;
  return stored === undefined || stored === null
    ? undefined
    : { value: String(stored), release };
}

function releasedFindings(
  prepared: PreparedCase,
  state: EncounterState,
): ReleasedFinding[] {
  return state.releases.flatMap((release) => {
    if (release.source.table !== "report") return [];
    const report = prepared.reports.get(release.source.id);
    const tests = new Set(
      [release.via, report?.test_item_id].filter(
        (t): t is string => typeof t === "string",
      ),
    );
    return (report?.findings ?? []).map((finding) => ({ finding, tests }));
  });
}

/** What the condition vocabulary can see of an encounter (Case Library SPEC §10.4). */
export function conditionContext(
  prepared: PreparedCase,
  state: EncounterState,
  commit: CommitFacts | null = null,
): ConditionContext {
  return {
    released: releasedIds(state),
    findings: releasedFindings(prepared, state),
    asked: new Set(state.asked),
    ordered: new Set(state.ordered.map((o) => o.item)),
    referred: new Set(state.referred),
    commit,
  };
}
