import type { Action } from "./actions.ts";
import type { ActionError } from "./errors.ts";
import type { PreparedCase } from "./prepare.ts";
import { releasedIds } from "./queries.ts";
import type { EncounterState } from "./encounter.ts";

export interface Commit {
  readonly at: number;
  readonly dx: string;
  readonly evidence: readonly string[];
  readonly plan: readonly string[];
  readonly note: string | null;
}

type CommitAction = Extract<Action, { kind: "commit" }>;

const PLAN_KINDS = new Set(["action", "referral"]);

function kindError(
  prepared: PreparedCase,
  id: string,
  expected: string,
  ok: (kind: string) => boolean,
): ActionError | null {
  const item = prepared.items.get(id);
  if (item === undefined)
    return { code: "unknown_item", message: `"${id}" is not in the catalogue` };
  return ok(item.kind)
    ? null
    : {
        code: "wrong_kind",
        message: `"${id}" is a ${item.kind} item, not ${expected}`,
      };
}

/** Checks a commit (SPEC §5.12): a diagnosis, evidence the Chart holds, and a plan of actions and referrals. */
export function checkCommit(
  prepared: PreparedCase,
  state: EncounterState,
  action: CommitAction,
): ActionError | null {
  const dxError = kindError(
    prepared,
    action.dx,
    "a diagnosis",
    (kind) => kind === "diagnosis",
  );
  if (dxError !== null) return dxError;
  const released = releasedIds(state);
  const unreleased = action.evidence.find((id) => !released.has(id));
  if (unreleased !== undefined) {
    return {
      code: "evidence_not_released",
      message: `"${unreleased}" is not in the Chart, so it cannot be cited`,
    };
  }
  for (const id of action.plan) {
    const error = kindError(prepared, id, "an action or a referral", (kind) =>
      PLAN_KINDS.has(kind),
    );
    if (error !== null) return error;
  }
  return null;
}

export function commitOf(state: EncounterState, action: CommitAction): Commit {
  return {
    at: state.clock,
    dx: action.dx,
    evidence: action.evidence,
    plan: action.plan,
    note: action.note ?? null,
  };
}
