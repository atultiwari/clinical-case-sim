import type { Action } from "@nidana/engine";
import type postgres from "postgres";
import { storedFromBody, type BundleSource } from "./bundles";
import type {
  EncounterRecord,
  EncounterStore,
  PlayerRecord,
  ScoreRecord,
} from "./store";

/**
 * Postgres implementations, used through the least-privilege role nidana_server
 * (supabase/proposed/20260926190000_play_schema.sql).
 */

type Sql = postgres.Sql | postgres.TransactionSql;

/** Published bundles from the Case Vault (development). */
export function pgBundleSource(sql: Sql): BundleSource {
  return {
    async listPublished() {
      const rows = await sql<{ id: string }[]>`
        select id from casevault.bundle where published_at is not null order by id`;
      return rows.map((r) => r.id);
    },
    async read(id) {
      const rows = await sql<
        { id: string; body: unknown; sha256: string | null }[]
      >`
        select id, body, sha256 from casevault.bundle where id = ${id} and published_at is not null`;
      const row = rows[0];
      return row === undefined
        ? null
        : storedFromBody(row.id, row.body, row.sha256 ?? "");
    },
  };
}

interface EncounterRow {
  id: string;
  player_id: string;
  bundle_id: string;
  difficulty: EncounterRecord["difficulty"];
  status: EncounterRecord["status"];
  started_at: Date;
  ended_at: Date | null;
}

interface PlayerRow {
  id: string;
  display_name: string;
  training_level: PlayerRecord["trainingLevel"];
  consent_research: boolean;
  created_at: Date;
}

const toPlayer = (row: PlayerRow): PlayerRecord => ({
  id: row.id,
  nickname: row.display_name,
  trainingLevel: row.training_level,
  consentResearch: row.consent_research,
  joinedAt: row.created_at,
});

const toRecord = (row: EncounterRow): EncounterRecord => ({
  id: row.id,
  playerId: row.player_id,
  bundleId: row.bundle_id,
  difficulty: row.difficulty,
  status: row.status,
  startedAt: row.started_at,
  endedAt: row.ended_at,
});

function targetOf(action: Action): string | null {
  return "item" in action
    ? action.item
    : action.kind === "commit"
      ? action.dx
      : null;
}

async function insertAction(
  sql: Sql,
  id: string,
  seq: number,
  action: Action,
): Promise<boolean> {
  // "on conflict do nothing" reports a clash without an error, which would abort a surrounding transaction.
  const rows = await sql`
    insert into play.action (encounter_id, seq, kind, target, payload)
    values (${id}, ${seq}, ${action.kind}, ${targetOf(action)}, ${sql.json(action as unknown as postgres.JSONValue)})
    on conflict (encounter_id, seq) do nothing
    returning seq`;
  return rows.length === 1;
}

/** Runs `work` in a transaction, or a savepoint when already inside one (tests). */
function atomically<T>(
  sql: Sql,
  work: (tx: postgres.TransactionSql) => Promise<T>,
): Promise<T> {
  return (
    "savepoint" in sql ? sql.savepoint(work) : sql.begin(work)
  ) as Promise<T>;
}

class Rollback extends Error {}

function finiteNumber(value: string, id: string): number {
  const number = Number(value);
  if (!Number.isFinite(number))
    throw new Error(`play.score for ${id} holds a total that is not a number`);
  return number;
}

export function pgStore(sql: Sql): EncounterStore {
  return {
    async getPlayer(playerId) {
      const rows = await sql<PlayerRow[]>`
        select id, display_name, training_level, consent_research, created_at
        from play.player where id = ${playerId}`;
      return rows[0] === undefined ? null : toPlayer(rows[0]);
    },
    async savePlayer(player) {
      // created_at records when the player agreed; an update never moves it.
      const rows = await sql<PlayerRow[]>`
        insert into play.player (id, display_name, training_level, consent_research)
        values (${player.id}, ${player.nickname}, ${player.trainingLevel}, ${player.consentResearch})
        on conflict (id) do update set
          display_name = excluded.display_name,
          training_level = excluded.training_level,
          consent_research = excluded.consent_research
        returning id, display_name, training_level, consent_research, created_at`;
      return toPlayer(rows[0] as PlayerRow);
    },
    async listEncounters(playerId) {
      const rows = await sql<(EncounterRow & { total: string | null })[]>`
        select e.id, e.player_id, e.bundle_id, e.difficulty, e.status, e.started_at, e.ended_at, s.total
        from play.encounter e left join play.score s on s.encounter_id = e.id
        where e.player_id = ${playerId}
        order by e.started_at desc
        limit 100`;
      return rows.map((row) => ({
        record: toRecord(row),
        total: row.total === null ? null : finiteNumber(row.total, row.id),
      }));
    },
    async create(record) {
      await sql`
        insert into play.encounter (id, player_id, bundle_id, difficulty, status, started_at)
        values (${record.id}, ${record.playerId}, ${record.bundleId}, ${record.difficulty}, ${record.status}, ${record.startedAt})`;
    },
    async get(id) {
      const rows = await sql<EncounterRow[]>`
        select id, player_id, bundle_id, difficulty, status, started_at, ended_at
        from play.encounter where id = ${id}`;
      return rows[0] === undefined ? null : toRecord(rows[0]);
    },
    async actions(id) {
      const rows = await sql<{ payload: Action }[]>`
        select payload from play.action where encounter_id = ${id} order by seq`;
      return rows.map((r) => r.payload);
    },
    append: (id, seq, action) => insertAction(sql, id, seq, action),
    async commit(id, seq, action, score: ScoreRecord, endedAt) {
      try {
        return await atomically(sql, async (tx) => {
          const closed = await tx`
            update play.encounter set status = 'committed', ended_at = ${endedAt}
            where id = ${id} and status = 'active' returning id`;
          if (closed.length === 0 || !(await insertAction(tx, id, seq, action)))
            throw new Rollback();
          await tx`
            insert into play.score (encounter_id, dx_score, total, breakdown, scoring_version, engine_version)
            values (${id}, ${score.dxScore}, ${score.total}, ${tx.json(score.breakdown as unknown as postgres.JSONValue)},
                    ${score.scoringVersion}, ${score.engineVersion})`;
          return true;
        });
      } catch (error: unknown) {
        if (error instanceof Rollback) return false;
        throw error;
      }
    },
    async score(id) {
      const rows = await sql<
        {
          dx_score: number;
          total: string;
          breakdown: ScoreRecord["breakdown"];
          scoring_version: string;
          engine_version: string;
        }[]
      >`select dx_score, total, breakdown, scoring_version, engine_version from play.score where encounter_id = ${id}`;
      const row = rows[0];
      return row === undefined
        ? null
        : {
            dxScore: row.dx_score,
            total: finiteNumber(row.total, id),
            breakdown: row.breakdown,
            scoringVersion: row.scoring_version,
            engineVersion: row.engine_version,
          };
    },
    async logMissing(request) {
      await sql`
        insert into play.missing_request (bundle_id, kind, query)
        values (${request.bundleId}, ${request.kind}, ${request.query})`;
    },
  };
}
