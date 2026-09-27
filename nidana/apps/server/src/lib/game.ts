import {
  Action,
  Difficulty,
  ENGINE_VERSION,
  applyAction,
  buildDebrief,
  replay,
  scoreEncounter,
  type DifficultySettings,
  type EncounterState,
  type PreparedCase,
  type Score,
  type ScoringSettings,
} from "@nidana/engine";
import { z } from "zod";
import type {
  Credits,
  DebriefView,
  EncounterSummary,
  Profile,
  TrainingLevel,
} from "@nidana/contracts";
import type { Player } from "./auth";
import { BundleRefusedError } from "./bundles";
import { buildDebriefView } from "./debrief-view";
import {
  cardOf,
  visibleTo,
  type BundleRegistry,
  type CaseCard,
} from "./registry";
import type { EncounterRecord, EncounterStore, PlayerRecord } from "./store";
import { buildPlayerView, sourceOfRef, type PlayerView } from "./view";

/**
 * The game service behind the route handlers (SPEC §6.2). Every function takes the signed-in
 * player's id and returns an outcome; nothing here trusts the request body.
 */

export interface GameDeps {
  readonly registry: BundleRegistry;
  readonly store: EncounterStore;
  readonly settings: DifficultySettings;
  readonly scoring: ScoringSettings;
  readonly newId: () => string;
  readonly now: () => Date;
}

export interface ApiError {
  readonly status: number;
  readonly code: string;
  readonly message: string;
}

export type Outcome<T> =
  | { readonly ok: true; readonly data: T }
  | { readonly ok: false; readonly error: ApiError };

const ok = <T>(data: T): Outcome<T> => ({ ok: true, data });
const fail = (
  status: number,
  code: string,
  message: string,
): Outcome<never> => ({
  ok: false,
  error: { status, code, message },
});
const notFound = (): Outcome<never> =>
  fail(404, "not_found", "No such encounter");

function invalid(error: z.ZodError): Outcome<never> {
  return fail(400, "invalid_request", z.prettifyError(error));
}

interface Loaded {
  readonly record: EncounterRecord;
  readonly prepared: PreparedCase;
  readonly actions: readonly Action[];
  readonly state: EncounterState;
}

async function loadEncounter(
  deps: GameDeps,
  playerId: string,
  encounterId: string,
): Promise<Outcome<Loaded>> {
  const record = await deps.store.get(encounterId);
  // Another player's encounter looks exactly like a missing one.
  if (record === null || record.playerId !== playerId) return notFound();
  let prepared: PreparedCase;
  try {
    prepared = await deps.registry.load(record.bundleId);
  } catch (error: unknown) {
    if (error instanceof BundleRefusedError) {
      return fail(
        503,
        "case_unavailable",
        "This case is not available at the moment",
      );
    }
    throw error;
  }
  const actions = await deps.store.actions(encounterId);
  return ok({
    record,
    prepared,
    actions,
    state: replay(prepared, deps.settings, record.difficulty, actions),
  });
}

export async function listCases(
  deps: GameDeps,
  player: Player,
): Promise<Outcome<readonly CaseCard[]>> {
  return ok(await deps.registry.cases(player.role));
}

const StartRequest = z.strictObject({
  slug: z.string().regex(/^c-[a-z0-9]{5}$/),
  difficulty: Difficulty,
});

export async function startEncounter(
  deps: GameDeps,
  player: Player,
  body: unknown,
): Promise<Outcome<PlayerView>> {
  const parsed = StartRequest.safeParse(body);
  if (!parsed.success) return invalid(parsed.error);
  if ((await deps.store.getPlayer(player.playerId)) === null) {
    return fail(
      403,
      "consent_required",
      "Agree to the consent screen before playing",
    );
  }
  const prepared = (await deps.registry.newestBySlug()).get(parsed.data.slug);
  if (prepared === undefined || !visibleTo(prepared, player.role))
    return fail(404, "not_found", "No such case");
  const playerId = player.playerId;
  const record: EncounterRecord = {
    id: deps.newId(),
    playerId,
    bundleId: prepared.bundle.bundle_id,
    difficulty: parsed.data.difficulty,
    status: "active",
    startedAt: deps.now(),
    endedAt: null,
  };
  await deps.store.create(record);
  return ok(
    buildPlayerView(
      prepared,
      replay(prepared, deps.settings, record.difficulty, []),
      record.id,
    ),
  );
}

export async function getView(
  deps: GameDeps,
  playerId: string,
  encounterId: string,
): Promise<Outcome<PlayerView>> {
  const loaded = await loadEncounter(deps, playerId, encounterId);
  if (!loaded.ok) return loaded;
  return ok(
    buildPlayerView(loaded.data.prepared, loaded.data.state, encounterId),
  );
}

export async function act(
  deps: GameDeps,
  playerId: string,
  encounterId: string,
  body: unknown,
): Promise<Outcome<PlayerView>> {
  const parsed = Action.safeParse(body);
  if (!parsed.success) return invalid(parsed.error);
  if (parsed.data.kind === "commit")
    return fail(400, "invalid_request", "Commit through the commit endpoint");
  const loaded = await loadEncounter(deps, playerId, encounterId);
  if (!loaded.ok) return loaded;
  const { prepared, state, actions } = loaded.data;
  const result = applyAction(prepared, deps.settings, state, parsed.data);
  if (!result.ok) return fail(422, result.error.code, result.error.message);
  if (!(await deps.store.append(encounterId, actions.length, parsed.data))) {
    return fail(
      409,
      "conflict",
      "Another action was recorded at the same time; reload and try again",
    );
  }
  return ok(buildPlayerView(prepared, result.state, encounterId));
}

const CommitRequest = z.strictObject({
  dx: z.string().min(1),
  /** Chart references from the PlayerView (`c12`), not bundle ids. */
  evidence: z.array(z.string().regex(/^c\d+$/)),
  plan: z.array(z.string().min(1)),
  note: z.string().max(2000).optional(),
});

export interface CommitResult {
  readonly total: number;
  readonly diagnosisAnchor: number;
  readonly scoringVersion: string;
}

export async function commit(
  deps: GameDeps,
  playerId: string,
  encounterId: string,
  body: unknown,
): Promise<Outcome<CommitResult>> {
  const parsed = CommitRequest.safeParse(body);
  if (!parsed.success) return invalid(parsed.error);
  const loaded = await loadEncounter(deps, playerId, encounterId);
  if (!loaded.ok) return loaded;
  const { prepared, state, actions } = loaded.data;
  const evidence = parsed.data.evidence.map((ref) => sourceOfRef(state, ref));
  if (evidence.some((id) => id === null)) {
    return fail(
      422,
      "evidence_not_released",
      "Evidence must be items in the Chart",
    );
  }
  const action: Action = {
    kind: "commit",
    dx: parsed.data.dx,
    evidence: evidence as string[],
    plan: parsed.data.plan,
    ...(parsed.data.note === undefined ? {} : { note: parsed.data.note }),
  };
  const result = applyAction(prepared, deps.settings, state, action);
  if (!result.ok) return fail(422, result.error.code, result.error.message);
  const score: Score = scoreEncounter(
    prepared,
    deps.settings,
    deps.scoring,
    result.state,
  );
  const stored = await deps.store.commit(
    encounterId,
    actions.length,
    action,
    {
      dxScore: score.diagnosis.anchor,
      total: score.total,
      breakdown: score,
      scoringVersion: score.version,
      engineVersion: ENGINE_VERSION,
    },
    deps.now(),
  );
  if (!stored)
    return fail(
      409,
      "conflict",
      "The encounter changed at the same time; reload and try again",
    );
  return ok({
    total: score.total,
    diagnosisAnchor: score.diagnosis.anchor,
    scoringVersion: score.version,
  });
}

export async function getDebrief(
  deps: GameDeps,
  playerId: string,
  encounterId: string,
): Promise<Outcome<DebriefView>> {
  const loaded = await loadEncounter(deps, playerId, encounterId);
  if (!loaded.ok) return loaded;
  const { prepared, state } = loaded.data;
  if (state.commit === null)
    return fail(409, "not_committed", "The debrief opens after the commit");
  return ok(
    buildDebriefView(
      prepared,
      state,
      buildDebrief(prepared, deps.settings, deps.scoring, state),
    ),
  );
}

const MissingRequestBody = z.strictObject({
  encounterId: z.string().min(1),
  kind: z.enum(["history", "exam", "test", "referral", "action", "diagnosis"]),
  query: z.string().trim().min(1).max(200),
});

/** Logs a search with no match (SPEC §6.2, N1.7). Costs nothing and stores no player identity. */
export async function logMissing(
  deps: GameDeps,
  playerId: string,
  body: unknown,
): Promise<Outcome<{ logged: true }>> {
  const parsed = MissingRequestBody.safeParse(body);
  if (!parsed.success) return invalid(parsed.error);
  const record = await deps.store.get(parsed.data.encounterId);
  if (record === null || record.playerId !== playerId) return notFound();
  await deps.store.logMissing({
    bundleId: record.bundleId,
    kind: parsed.data.kind,
    query: parsed.data.query,
  });
  return ok({ logged: true });
}

const TRAINING_LEVELS = [
  "mbbs_student",
  "intern",
  "resident",
  "consultant",
  "other",
] as const satisfies readonly TrainingLevel[];

const SaveProfileBody = z.strictObject({
  // A nickname, not a name: letters, digits, spaces and . _ ' - only, and never an email address.
  nickname: z
    .string()
    .trim()
    .min(2)
    .max(24)
    .regex(
      /^[\p{L}\p{N} ._'-]+$/u,
      "Use letters, digits, spaces and . _ ' - only",
    ),
  trainingLevel: z.enum(TRAINING_LEVELS),
  consentResearch: z.boolean(),
  agreed: z.literal(true),
});

function profileOf(record: PlayerRecord, player: Player): Profile {
  return {
    nickname: record.nickname,
    trainingLevel: record.trainingLevel,
    consentResearch: record.consentResearch,
    joinedAt: record.joinedAt.toISOString(),
    role: player.role,
  };
}

/** The signed-in player's profile; 404 until they have agreed on the consent screen. */
export async function getMe(
  deps: GameDeps,
  player: Player,
): Promise<Outcome<Profile>> {
  const record = await deps.store.getPlayer(player.playerId);
  return record === null
    ? fail(404, "no_profile", "No profile yet")
    : ok(profileOf(record, player));
}

/** Creates the profile on consent, or updates the nickname, training level and research consent. */
export async function saveMe(
  deps: GameDeps,
  player: Player,
  body: unknown,
): Promise<Outcome<Profile>> {
  const parsed = SaveProfileBody.safeParse(body);
  if (!parsed.success) return invalid(parsed.error);
  const saved = await deps.store.savePlayer({
    id: player.playerId,
    nickname: parsed.data.nickname,
    trainingLevel: parsed.data.trainingLevel,
    consentResearch: parsed.data.consentResearch,
    joinedAt: deps.now(),
  });
  return ok(profileOf(saved, player));
}

/** The signed-in player's own encounters, and nobody else's (N1.6). */
export async function listMyEncounters(
  deps: GameDeps,
  player: Player,
): Promise<Outcome<readonly EncounterSummary[]>> {
  const rows = await deps.store.listEncounters(player.playerId);
  const summaries = await Promise.all(
    rows.map(async ({ record, total }) => {
      const card = await deps.registry
        .load(record.bundleId)
        .then(cardOf, () => null);
      return {
        encounterId: record.id,
        caseSlug: card?.slug ?? "",
        caseTitle: card?.title ?? "A case that is no longer available",
        difficulty: record.difficulty,
        status: record.status,
        startedAt: record.startedAt.toISOString(),
        total,
      };
    }),
  );
  return ok(summaries);
}

export const ATTRIBUTION_STATEMENT =
  "Every case is adapted from a published, openly licensed case report, restructured into a simulation: the diagnosis is hidden until the debrief, and simulated findings are added where marked.";

/** The attribution of every case the player can see (SPEC §12), with the general statement. */
export async function credits(
  deps: GameDeps,
  player: Player,
): Promise<Outcome<Credits>> {
  const cases = [...(await deps.registry.newestBySlug()).values()].filter((p) =>
    visibleTo(p, player.role),
  );
  const sources = cases
    .map((p) => p.bundle.source)
    .filter((s): s is NonNullable<typeof s> => s !== null)
    .map((s) => ({
      citation: s.citation ?? null,
      licence: s.licence,
      attribution: s.attribution ?? null,
      url: s.url ?? null,
    }))
    .sort((a, b) => (a.citation ?? "").localeCompare(b.citation ?? ""));
  return ok({ statement: ATTRIBUTION_STATEMENT, sources });
}
