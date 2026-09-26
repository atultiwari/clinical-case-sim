import { z } from "zod";
import { ACTION_ITEM_KIND, Action, SEAT, type ItemAction } from "./actions.ts";
import { EngineError, type ActionError } from "./errors.ts";
import type { PreparedCase } from "./prepare.ts";
import { conditionContext } from "./queries.ts";
import {
  answerItem,
  consultFor,
  resultsForTest,
  type ReleaseDraft,
} from "./resolve.ts";
import type { Difficulty, DifficultySettings, Level } from "./settings.ts";

/**
 * `state = replay(case, settings, difficulty, actions)` (SPEC §6.1): a pure fold over the action
 * log. The state holds everything that follows from the log, including results not yet due, so
 * the same bundle revision and the same actions always give the same state (invariant I6).
 */

export const MINUTES_PER_DAY = 1440;

export interface Release extends ReleaseDraft {
  /** Simulated minute at which it reached the Chart. */
  readonly at: number;
  /** Position in the action log; -1 for the vignette. */
  readonly actionIndex: number;
}

export interface Pending {
  readonly actionIndex: number;
  readonly kind: "order" | "referral";
  readonly item: string;
  readonly orderedAt: number;
  readonly dueAt: number;
  /** Resolved when ordered; they reach the Chart at `dueAt`. */
  readonly releases: readonly Release[];
}

export interface Limits {
  readonly budget: number;
  readonly maxStayMinutes: number;
  readonly referralsAllowed: number;
}

export interface EncounterState {
  readonly difficulty: Difficulty;
  readonly actionCount: number;
  /** Simulated minutes since arrival on day 0. */
  readonly clock: number;
  /** INR spent on orders. */
  readonly spend: number;
  readonly releases: readonly Release[];
  readonly pending: readonly Pending[];
  readonly asked: readonly string[];
  readonly examined: readonly string[];
  readonly ordered: readonly { readonly item: string; readonly at: number }[];
  readonly referred: readonly string[];
  readonly differential: readonly {
    readonly at: number;
    readonly items: readonly string[];
  }[];
  readonly limits: Limits;
  /** Set when a limit is reached; only a commit is accepted after it. */
  readonly mustCommit: "max_stay" | null;
}

export type ActionResult =
  | { readonly ok: true; readonly state: EncounterState }
  | { readonly ok: false; readonly error: ActionError };

export const dayOf = (minute: number): number =>
  Math.floor(minute / MINUTES_PER_DAY);

const levelOf = (settings: DifficultySettings, difficulty: Difficulty): Level =>
  settings.difficulties[difficulty];

export function initialState(
  prepared: PreparedCase,
  settings: DifficultySettings,
  difficulty: Difficulty,
): EncounterState {
  const level = levelOf(settings, difficulty);
  const vignette: Release[] = prepared.vignetteFacts.map((fact) => ({
    at: 0,
    actionIndex: -1,
    via: null,
    source: { table: "fact", id: fact.id },
    component: null,
    day: fact.day,
    requestedDay: null,
  }));
  return {
    difficulty,
    actionCount: 0,
    clock: 0,
    spend: 0,
    releases: vignette,
    pending: [],
    asked: [],
    examined: [],
    ordered: [],
    referred: [],
    differential: [],
    limits: {
      budget: Math.round(prepared.efficientPathCost * level.budget_factor),
      maxStayMinutes: settings.clock.max_stay_minutes,
      referralsAllowed: level.referrals_allowed,
    },
    mustCommit: null,
  };
}

/** Moves the clock forward (never past the maximum stay) and delivers what falls due, in due order. */
function advance(state: EncounterState, to: number): EncounterState {
  const clock = Math.min(
    Math.max(to, state.clock),
    state.limits.maxStayMinutes,
  );
  const due = state.pending
    .filter((p) => p.dueAt <= clock)
    .sort((a, b) => a.dueAt - b.dueAt || a.actionIndex - b.actionIndex);
  return {
    ...state,
    clock,
    releases: [...state.releases, ...due.flatMap((p) => p.releases)],
    pending: state.pending.filter((p) => p.dueAt > clock),
    mustCommit:
      clock >= state.limits.maxStayMinutes ? "max_stay" : state.mustCommit,
  };
}

const refuse = (error: ActionError): ActionResult => ({ ok: false, error });

function stamp(
  drafts: readonly ReleaseDraft[],
  at: number,
  actionIndex: number,
): Release[] {
  return drafts.map((d) => ({ ...d, at, actionIndex }));
}

function checkItem(
  prepared: PreparedCase,
  action: ItemAction,
): ActionError | null {
  const item = prepared.items.get(action.item);
  if (item === undefined)
    return {
      code: "unknown_item",
      message: `"${action.item}" is not in the catalogue`,
    };
  const kind = ACTION_ITEM_KIND[action.kind];
  if (item.kind !== kind) {
    return {
      code: "wrong_kind",
      message: `"${action.item}" is a ${item.kind} item; ${action.kind} takes a ${kind} item`,
    };
  }
  if (!item.specialty_scope.includes(SEAT)) {
    return {
      code: "not_available_to_seat",
      message: `"${action.item}" is not available to the ${SEAT} seat`,
    };
  }
  return null;
}

function applyQuestion(
  prepared: PreparedCase,
  settings: DifficultySettings,
  state: EncounterState,
  action: Extract<Action, { kind: "ask" | "examine" }>,
): EncounterState {
  const minutes =
    action.kind === "ask"
      ? settings.clock.ask_minutes
      : settings.clock.examine_minutes;
  const day = dayOf(state.clock);
  const next = advance(state, state.clock + minutes);
  const answers = stamp(
    answerItem(prepared, action.item, day),
    next.clock,
    state.actionCount,
  );
  return {
    ...next,
    releases: [...next.releases, ...answers],
    asked: action.kind === "ask" ? [...next.asked, action.item] : next.asked,
    examined:
      action.kind === "examine"
        ? [...next.examined, action.item]
        : next.examined,
  };
}

function applyOrder(
  prepared: PreparedCase,
  settings: DifficultySettings,
  state: EncounterState,
  item: string,
): ActionResult {
  const test = prepared.tests.get(item);
  if (test === undefined) {
    return refuse({
      code: "not_orderable",
      message: `"${item}" has no price or turnaround in the catalogue`,
    });
  }
  const price = test.price_inr ?? 0;
  if (state.spend + price > state.limits.budget) {
    return refuse({
      code: "over_budget",
      message: `"${item}" costs ₹${price}; ₹${state.limits.budget - state.spend} of the budget is left`,
    });
  }
  const dueAt = state.clock + (test.tat_minutes ?? 0);
  const drafts = resultsForTest(
    prepared,
    item,
    dayOf(state.clock),
    levelOf(settings, state.difficulty),
  );
  const pending: Pending = {
    actionIndex: state.actionCount,
    kind: "order",
    item,
    orderedAt: state.clock,
    dueAt,
    releases: stamp(drafts, dueAt, state.actionCount),
  };
  const next = {
    ...state,
    spend: state.spend + price,
    ordered: [...state.ordered, { item, at: state.clock }],
    pending: [...state.pending, pending],
  };
  return { ok: true, state: advance(next, next.clock) };
}

function applyReferral(
  prepared: PreparedCase,
  settings: DifficultySettings,
  state: EncounterState,
  item: string,
): ActionResult {
  if (state.referred.length >= state.limits.referralsAllowed) {
    return refuse({
      code: "referral_limit",
      message: `${state.limits.referralsAllowed} referrals are allowed at this difficulty`,
    });
  }
  const dueAt = state.clock + settings.clock.referral_minutes;
  const note = consultFor(
    prepared,
    item,
    dayOf(state.clock),
    conditionContext(prepared, state),
  );
  const pending: Pending = {
    actionIndex: state.actionCount,
    kind: "referral",
    item,
    orderedAt: state.clock,
    dueAt,
    releases: stamp([note], dueAt, state.actionCount),
  };
  return {
    ok: true,
    state: {
      ...state,
      referred: [...state.referred, item],
      pending: [...state.pending, pending],
    },
  };
}

function applyWait(
  state: EncounterState,
  minutes: number | undefined,
): EncounterState {
  if (minutes !== undefined) return advance(state, state.clock + minutes);
  const nextDue = Math.min(...state.pending.map((p) => p.dueAt));
  const target = Number.isFinite(nextDue)
    ? nextDue
    : (dayOf(state.clock) + 1) * MINUTES_PER_DAY;
  return advance(state, target);
}

function applyDifferential(
  prepared: PreparedCase,
  state: EncounterState,
  items: readonly string[],
): ActionResult {
  const wrong = items.find(
    (id) => prepared.items.get(id)?.kind !== "diagnosis",
  );
  if (wrong !== undefined) {
    const known = prepared.items.has(wrong);
    return refuse({
      code: known ? "wrong_kind" : "unknown_item",
      message: known
        ? `"${wrong}" is not a diagnosis`
        : `"${wrong}" is not in the catalogue`,
    });
  }
  return {
    ok: true,
    state: {
      ...state,
      differential: [...state.differential, { at: state.clock, items }],
    },
  };
}

function dispatch(
  prepared: PreparedCase,
  settings: DifficultySettings,
  state: EncounterState,
  action: Action,
): ActionResult {
  switch (action.kind) {
    case "ask":
    case "examine":
      return {
        ok: true,
        state: applyQuestion(prepared, settings, state, action),
      };
    case "order":
      return applyOrder(prepared, settings, state, action.item);
    case "refer":
      return applyReferral(prepared, settings, state, action.item);
    case "wait":
      return { ok: true, state: applyWait(state, action.minutes) };
    case "differential":
      return applyDifferential(prepared, state, action.items);
  }
}

/** Validates one action and returns the next state, or why the action is refused. Never throws for bad input. */
export function applyAction(
  prepared: PreparedCase,
  settings: DifficultySettings,
  state: EncounterState,
  input: unknown,
): ActionResult {
  const parsed = Action.safeParse(input);
  if (!parsed.success)
    return refuse({
      code: "invalid_action",
      message: z.prettifyError(parsed.error),
    });
  const action = parsed.data;
  if (state.mustCommit !== null) {
    return refuse({
      code: "must_commit",
      message: "A limit has been reached; the encounter can only be committed",
    });
  }
  if ("item" in action) {
    const error = checkItem(prepared, action);
    if (error !== null) return refuse(error);
  }
  const result = dispatch(prepared, settings, state, action);
  return result.ok
    ? {
        ok: true,
        state: { ...result.state, actionCount: state.actionCount + 1 },
      }
    : result;
}

function describe(action: Action): string {
  return "item" in action ? `${action.kind} ${action.item}` : action.kind;
}

/** Replays a stored action log. A refused action means the log is corrupt, so it throws. */
export function replay(
  prepared: PreparedCase,
  settings: DifficultySettings,
  difficulty: Difficulty,
  actions: readonly Action[],
): EncounterState {
  return actions.reduce(
    (state, action, index) => {
      const result = applyAction(prepared, settings, state, action);
      if (!result.ok) {
        throw new EngineError(
          result.error.code,
          `action ${index + 1} (${describe(action)}) was refused: ${result.error.code}: ${result.error.message}`,
        );
      }
      return result.state;
    },
    initialState(prepared, settings, difficulty),
  );
}
