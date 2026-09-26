import type { Action, Difficulty, Score } from "@nidana/engine";

/** Play data (SPEC §8.2). The action log is append-only (invariant I5); state is never stored. */

export type EncounterStatus = "active" | "committed";

export interface EncounterRecord {
  readonly id: string;
  readonly playerId: string;
  /** The bundle revision the encounter uses (invariant I5). */
  readonly bundleId: string;
  readonly difficulty: Difficulty;
  readonly status: EncounterStatus;
  readonly startedAt: Date;
  readonly endedAt: Date | null;
}

export interface ScoreRecord {
  readonly dxScore: number;
  readonly total: number;
  readonly breakdown: Score;
  readonly scoringVersion: string;
  readonly engineVersion: string;
}

export interface MissingRequest {
  readonly bundleId: string;
  readonly kind: string;
  readonly query: string;
}

export interface EncounterStore {
  /** Creates the minimal player row the encounter refers to, if it does not exist. */
  ensurePlayer(playerId: string): Promise<void>;
  create(record: EncounterRecord): Promise<void>;
  get(id: string): Promise<EncounterRecord | null>;
  /** The action log, in order. */
  actions(id: string): Promise<readonly Action[]>;
  /** Appends at `seq`; false if another request took that position first. */
  append(id: string, seq: number, action: Action): Promise<boolean>;
  /** Appends the commit, stores the score and closes the encounter, all or nothing. */
  commit(
    id: string,
    seq: number,
    action: Action,
    score: ScoreRecord,
    endedAt: Date,
  ): Promise<boolean>;
  score(id: string): Promise<ScoreRecord | null>;
  /** Holds no player identity (SPEC §8.1). */
  logMissing(request: MissingRequest): Promise<void>;
}

/** For tests and local play without a database. Nothing survives a restart. */
export function memoryStore(): EncounterStore & {
  readonly missing: readonly MissingRequest[];
} {
  const players = new Set<string>();
  const encounters = new Map<string, EncounterRecord>();
  const logs = new Map<string, Action[]>();
  const scores = new Map<string, ScoreRecord>();
  const missing: MissingRequest[] = [];

  const appendAt = (id: string, seq: number, action: Action): boolean => {
    const log = logs.get(id) ?? [];
    if (log.length !== seq) return false;
    logs.set(id, [...log, action]);
    return true;
  };

  return {
    missing,
    ensurePlayer: async (playerId) => {
      players.add(playerId);
    },
    create: async (record) => {
      if (!players.has(record.playerId))
        throw new Error(`unknown player ${record.playerId}`);
      encounters.set(record.id, record);
      logs.set(record.id, []);
    },
    get: async (id) => encounters.get(id) ?? null,
    actions: async (id) => logs.get(id) ?? [],
    append: async (id, seq, action) => appendAt(id, seq, action),
    commit: async (id, seq, action, score, endedAt) => {
      const record = encounters.get(id);
      if (
        record === undefined ||
        record.status !== "active" ||
        !appendAt(id, seq, action)
      )
        return false;
      encounters.set(id, { ...record, status: "committed", endedAt });
      scores.set(id, score);
      return true;
    },
    score: async (id) => scores.get(id) ?? null,
    logMissing: async (request) => {
      missing.push(request);
    },
  };
}
