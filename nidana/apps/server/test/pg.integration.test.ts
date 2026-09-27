import { readFileSync } from "node:fs";
import postgres from "postgres";
import { describe, expect, it } from "vitest";
import type { Action } from "@nidana/engine";
import { pgBundleSource, pgStore } from "@/lib/pg";
import { createBundleRegistry } from "@/lib/registry";
import { EXPORTS_DIR, NIDANA_DIR, PILOT, catalogue } from "./helpers";

/**
 * Runs the proposed play migration against a local Case Vault database inside one transaction
 * that is always rolled back, so nothing persists. Set NIDANA_TEST_DB_URL to run it, e.g.
 * postgresql://postgres:postgres@127.0.0.1:55322/postgres (the Case Library's local stack).
 */
const url = process.env.NIDANA_TEST_DB_URL;
const MIGRATION = readFileSync(
  `${NIDANA_DIR}supabase/proposed/20260926190000_play_schema.sql`,
  "utf8",
);
/** Proposed after the play schema was applied (N1.6); safe to run again. */
const PLAYER_UPDATE = readFileSync(
  `${NIDANA_DIR}supabase/proposed/20260927090000_play_player_update.sql`,
  "utf8",
);
const PLAYER = "44444444-4444-4444-8444-444444444444";

class Rollback extends Error {}

async function inRolledBackTransaction(
  work: (tx: postgres.TransactionSql) => Promise<void>,
): Promise<void> {
  const sql = postgres(url ?? "", { max: 1, onnotice: () => undefined });
  try {
    await sql.begin(async (tx) => {
      await work(tx);
      throw new Rollback();
    });
  } catch (error: unknown) {
    if (!(error instanceof Rollback)) throw error;
  } finally {
    await sql.end();
  }
}

async function seed(tx: postgres.TransactionSql): Promise<void> {
  // The play schema may already be applied (the Case Library's local stack has it since L1.9).
  const [applied] =
    await tx`select exists (select 1 from pg_namespace where nspname = 'play') as present`;
  if (applied?.present !== true) await tx.unsafe(MIGRATION);
  await tx.unsafe(PLAYER_UPDATE);
  const body = JSON.parse(
    readFileSync(`${EXPORTS_DIR}${PILOT}.json`, "utf8"),
  ) as postgres.JSONValue;
  const sha = readFileSync(`${EXPORTS_DIR}${PILOT}.json.sha256`, "utf8")
    .trim()
    .split(/\s+/)[0];
  const [caseId, version] = ["PMC12949993", "PMC12949993@v1"];
  await tx`insert into casevault."case" (id, source_type, slug) values (${caseId}, 'de_novo', 'c-test1') on conflict do nothing`;
  await tx`insert into casevault.case_version (id, case_id, version, status) values (${version}, ${caseId}, 1, 'draft') on conflict do nothing`;
  await tx`insert into casevault.bundle (id, case_version_id, revision, catalogue_version, body, sha256, published_at)
           values (${PILOT}, ${version}, 3, 2, ${tx.json(body)}, ${sha ?? ""}, now())`;
  await tx`insert into casevault.bundle (id, case_version_id, revision, catalogue_version, body, sha256)
           values ('PMC12949993@v1.r9', ${version}, 9, 2, '{}', null)`;
  await tx`insert into auth.users (id, aud, role) values (${PLAYER}, 'authenticated', 'authenticated')`;
}

describe.skipIf(url === undefined)(
  "the play schema on Postgres (rolled back)",
  () => {
    it("lets nidana_server read published bundles only, and verifies their hash", async () => {
      await inRolledBackTransaction(async (tx) => {
        await seed(tx);
        await tx`set local role nidana_server`;
        const source = pgBundleSource(tx);
        expect(await source.listPublished()).toEqual([PILOT]);
        expect(await source.read("PMC12949993@v1.r9")).toBeNull();
        const prepared = await createBundleRegistry(source, catalogue).load(
          PILOT,
        );
        expect(prepared.bundle.bundle_id).toBe(PILOT);
      });
    });

    it("stores an encounter, its action log, the commit and the score through nidana_server", async () => {
      await inRolledBackTransaction(async (tx) => {
        await seed(tx);
        await tx`set local role nidana_server`;
        const store = pgStore(tx);
        const id = "55555555-5555-4555-8555-555555555555";
        const joined = await store.savePlayer({
          id: PLAYER,
          nickname: "Tester",
          trainingLevel: "resident",
          consentResearch: true,
          joinedAt: new Date(),
        });
        const updated = await store.savePlayer({
          ...joined,
          nickname: "Renamed",
          consentResearch: false,
        });
        expect(updated).toMatchObject({
          nickname: "Renamed",
          consentResearch: false,
          joinedAt: joined.joinedAt,
        });
        expect(await store.getPlayer(PLAYER)).toMatchObject({
          nickname: "Renamed",
        });
        await store.create({
          id,
          playerId: PLAYER,
          bundleId: PILOT,
          difficulty: "standard",
          status: "active",
          startedAt: new Date(),
          endedAt: null,
        });
        const ask: Action = { kind: "ask", item: "HX.MEDS.CURRENT" };
        expect(await store.append(id, 0, ask)).toBe(true);
        expect(await store.append(id, 0, { kind: "wait" })).toBe(false);
        expect(await store.actions(id)).toEqual([ask]);
        const commit: Action = {
          kind: "commit",
          dx: "DX.LEAD_POISONING",
          evidence: [],
          plan: [],
        };
        const score = {
          dxScore: 4,
          total: 61.5,
          breakdown: { version: "v" } as never,
          scoringVersion: "v",
          engineVersion: "0.1.0",
        };

        expect(await store.commit(id, 1, commit, score, new Date())).toBe(true);
        expect(await store.commit(id, 2, commit, score, new Date())).toBe(
          false,
        );
        expect((await store.get(id))?.status).toBe("committed");
        expect(await store.score(id)).toMatchObject({
          dxScore: 4,
          total: 61.5,
        });
        expect(await store.listEncounters(PLAYER)).toEqual([
          expect.objectContaining({
            total: 61.5,
            record: expect.objectContaining({ id, status: "committed" }),
          }),
        ]);
        expect(
          await store.listEncounters("99999999-9999-4999-8999-999999999999"),
        ).toEqual([]);
        await store.logMissing({
          bundleId: PILOT,
          kind: "test",
          query: "hair arsenic",
        });
        const refused = (query: string) =>
          expect(tx.savepoint((sp) => sp.unsafe(query))).rejects;
        await refused(
          `update play.action set target = 'x' where encounter_id = '${id}'`,
        ).toThrow(/permission denied/);
        await refused(
          `delete from play.action where encounter_id = '${id}'`,
        ).toThrow(/permission denied/);
        await refused("select * from play.missing_request").toThrow(
          /permission denied/,
        );
        await refused(
          `update play.encounter set difficulty = 'expert' where id = '${id}'`,
        ).toThrow(/permission denied/);
        // The owner has the privilege, and the triggers still refuse.
        await tx`reset role`;
        await refused(
          `update play.action set target = 'x' where encounter_id = '${id}'`,
        ).toThrow(/insert-only/);
        await refused(
          `update play.encounter set difficulty = 'expert' where id = '${id}'`,
        ).toThrow(/committed once/);
        // N1.7: the missing request holds the bundle, kind and query, and no player column.
        const columns = await tx<{ column_name: string }[]>`
          select column_name from information_schema.columns
          where table_schema = 'play' and table_name = 'missing_request'
          order by ordinal_position`;
        expect(columns.map((c) => c.column_name)).toEqual([
          "id",
          "created_at",
          "bundle_id",
          "kind",
          "query",
        ]);
        expect(
          await tx`select bundle_id, kind, query from play.missing_request where query = 'hair arsenic'`,
        ).toEqual([{ bundle_id: PILOT, kind: "test", query: "hair arsenic" }]);
      });
    });

    it("gives the public key's roles nothing in casevault or play", async () => {
      for (const role of ["anon", "authenticated"]) {
        for (const query of [
          "select * from play.encounter",
          "select * from play.action",
          "select id from casevault.bundle",
        ]) {
          await inRolledBackTransaction(async (tx) => {
            await seed(tx);
            await tx.unsafe(`set local role ${role}`);
            await expect(tx.unsafe(query)).rejects.toThrow(/permission denied/);
          });
        }
      }
    });
  },
);
