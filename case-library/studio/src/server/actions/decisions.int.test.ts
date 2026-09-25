/**
 * Integration tests for the Studio's writes, against the local Case Vault.
 * Skipped unless both are set:
 *   CASE_VAULT_DB_URL_STUDIO_WRITER  the writer URL (locally the superuser URL; the Studio switches role)
 *   CASE_VAULT_DB_URL_TEST_OWNER     a local owner URL, to seed and remove the test case
 * They seed the de novo case NID-9901@v1 and remove it, with its decisions, afterwards.
 */
import { randomBytes } from "node:crypto";

import postgres from "postgres";
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import { passwordVersion } from "@/lib/auth/config";
import { hashPassword } from "@/lib/auth/password";
import { isLocalHost, sessionCookie } from "@/lib/auth/request";
import { createSessionToken } from "@/lib/auth/session";

const request = vi.hoisted(() => ({
  headers: new Headers() as Headers,
  cookies: new Map<string, string>(),
}));

vi.mock("next/headers", () => ({
  headers: async () => request.headers,
  cookies: async () => ({
    get: (name: string) => (request.cookies.has(name) ? { name, value: request.cookies.get(name) } : undefined),
  }),
}));
vi.mock("next/cache", () => ({ revalidatePath: () => undefined }));

const { submitFigureDecision, submitReviewDecision } = await import("@/server/actions/decisions");
const { closeWriterDb, withWriter } = await import("@/server/writer-db");

const writerUrl = process.env.CASE_VAULT_DB_URL_STUDIO_WRITER;
const ownerUrl = process.env.CASE_VAULT_DB_URL_TEST_OWNER;
const ownerIsLocal = ownerUrl ? isLocalHost(new URL(ownerUrl).host) : false;

const CASE_ID = "NID-9901";
const CV = `${CASE_ID}@v1`;
const USER = "studiotest";
const SECRET = randomBytes(48).toString("base64");
const ORIGIN = { host: "localhost:3000", origin: "http://localhost:3000" };

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) data.set(key, value);
  return data;
}

describe.skipIf(!writerUrl || !ownerUrl || !ownerIsLocal)("Studio writes (local Case Vault)", () => {
  const owner = postgres(ownerUrl ?? "postgres://unused", { max: 1, prepare: false, onnotice: () => undefined });
  let token = "";
  const saved = { users: process.env.STUDIO_USERS, secret: process.env.STUDIO_SESSION_SECRET };

  async function cleanUp() {
    await owner.begin(async (sql) => {
      await sql`delete from casevault.review_decision where decided_by = ${USER}`;
      await sql`delete from casevault.review_batch where id like ${`studio-%-${USER}%`}`;
      await sql`delete from casevault.media where case_version_id = ${CV}`;
      await sql`delete from casevault.fact where case_version_id = ${CV}`;
      await sql`delete from casevault.case_version where id = ${CV}`;
      await sql`delete from casevault."case" where id = ${CASE_ID}`;
    });
  }

  async function decisionCount(): Promise<number> {
    const [row] = await owner<{ n: number }[]>`
      select count(*)::int as n from casevault.review_decision where decided_by = ${USER}`;
    return row?.n ?? 0;
  }

  beforeAll(async () => {
    await cleanUp();
    await owner.begin(async (sql) => {
      await sql`insert into casevault."case" (id, source_type) values (${CASE_ID}, 'de_novo')`;
      await sql`insert into casevault.case_version (id, case_id, version) values (${CV}, ${CASE_ID}, 1)`;
      await sql`
        insert into casevault.fact (case_version_id, id, category, item, origin, release, generator,
                                    skill_version, source_locator)
        values (${CV}, 'H01', 'history', 'Fatigue', 'article', 'chart', 'studio-int-test', 'v0', 'p1')`;
      await sql`insert into casevault.media (case_version_id, id, licence) values (${CV}, 'M01', 'CC BY 4.0')`;
    });
    const encoded = await hashPassword("integration password", { N: 2 ** 14, r: 8, p: 1 });
    process.env.STUDIO_USERS = `${USER}:${encoded}`;
    process.env.STUDIO_SESSION_SECRET = SECRET;
    token = createSessionToken(USER, passwordVersion(encoded), SECRET);
  });

  afterAll(async () => {
    process.env.STUDIO_USERS = saved.users;
    process.env.STUDIO_SESSION_SECRET = saved.secret;
    await cleanUp();
    await owner.end({ timeout: 5 });
    await closeWriterDb();
  });

  beforeEach(() => {
    request.headers = new Headers(ORIGIN);
    request.cookies = new Map();
  });

  function logIn(value = token) {
    request.cookies.set(sessionCookie(ORIGIN.host, process.env.NODE_ENV).name, value);
  }

  const approveH01 = () => form({ caseVersionId: CV, targetTable: "fact", rowId: "H01", decision: "approve" });

  it("writes as casevault_studio_writer in a read-write transaction", async () => {
    const [row] = await withWriter((sql) => sql<{ role: string }[]>`select current_user as role`);
    expect(row?.role).toBe("casevault_studio_writer");
  });

  it("refuses a logged-out request", async () => {
    const before = await decisionCount();
    const result = await submitReviewDecision(null, approveH01());
    expect(result).toMatchObject({ ok: false, message: expect.stringMatching(/session/i) });
    expect(await submitFigureDecision(null, form({ caseVersionId: CV, mediaId: "M01", decision: "use" }))).toMatchObject({
      ok: false,
    });
    expect(await decisionCount()).toBe(before);
  });

  it("refuses a tampered session cookie", async () => {
    logIn(`${token.slice(0, -2)}AA`);
    expect(await submitReviewDecision(null, approveH01())).toMatchObject({ ok: false });
  });

  it("refuses a request from another origin even with a valid session", async () => {
    logIn();
    request.headers = new Headers({ host: ORIGIN.host, origin: "https://evil.example" });
    expect(await submitReviewDecision(null, approveH01())).toMatchObject({ ok: false, message: expect.stringMatching(/Studio/) });
  });

  it("refuses every write without a login configured (v1)", async () => {
    logIn();
    const users = process.env.STUDIO_USERS;
    process.env.STUDIO_USERS = "";
    try {
      expect(await submitReviewDecision(null, approveH01())).toMatchObject({ ok: false, message: expect.stringMatching(/Read-only/) });
    } finally {
      process.env.STUDIO_USERS = users;
    }
  });

  it("records a logged-in review decision in review_decision under today's Studio batch", async () => {
    logIn();
    const edit = form({ caseVersionId: CV, targetTable: "fact", rowId: "H01", decision: "edit", edited: "Tiredness", note: "lay term" });
    const result = await submitReviewDecision(null, edit);
    expect(result).toMatchObject({ ok: true });
    const batch = `studio-${new Date().toISOString().slice(0, 10)}-${USER}`;
    const rows = await owner`
      select d.batch_id, d.target_table, d.target_id, d.decision, d.edited, d.note, d.decided_by, b.case_version_ids
      from casevault.review_decision d join casevault.review_batch b on b.id = d.batch_id
      where d.decided_by = ${USER}`;
    expect(rows).toEqual([
      {
        batch_id: batch,
        target_table: "fact",
        target_id: `${CV}/H01`,
        decision: "edit",
        edited: "Tiredness",
        note: "lay term",
        decided_by: USER,
        case_version_ids: [CV],
      },
    ]);
  });

  it("stores a JSON edit as JSON, in the same open batch", async () => {
    logIn();
    const edit = form({ caseVersionId: CV, targetTable: "fact", rowId: "H01", decision: "edit", edited: '{"value": 80}' });
    expect(await submitReviewDecision(null, edit)).toMatchObject({ ok: true });
    const rows = await owner<{ edited: unknown; batches: number }[]>`
      select d.edited, (select count(*)::int from casevault.review_batch where id like ${`studio-%-${USER}%`}) as batches
      from casevault.review_decision d where d.decided_by = ${USER} order by d.id desc limit 1`;
    expect(rows[0]).toEqual({ edited: { value: 80 }, batches: 1 });
  });

  it("refuses a row that is not in the case version", async () => {
    logIn();
    const result = await submitReviewDecision(null, form({ caseVersionId: CV, targetTable: "fact", rowId: "H99", decision: "approve" }));
    expect(result).toMatchObject({ ok: false, message: expect.stringMatching(/not part of this case version/) });
  });

  it("records a logged-in figure decision on the media row", async () => {
    logIn();
    const result = await submitFigureDecision(
      null,
      form({ caseVersionId: CV, mediaId: "M01", decision: "mask", maskedPath: `${CASE_ID}/M01-masked.png` }),
    );
    expect(result).toMatchObject({ ok: true });
    const [row] = await owner`
      select production_decision, masked_path, decided_by, decided_at is not null as dated
      from casevault.media where case_version_id = ${CV} and id = 'M01'`;
    expect(row).toEqual({ production_decision: "mask", masked_path: `${CASE_ID}/M01-masked.png`, decided_by: USER, dated: true });
  });

  it("refuses a mask without a safe masked path", async () => {
    logIn();
    const result = await submitFigureDecision(
      null,
      form({ caseVersionId: CV, mediaId: "M01", decision: "mask", maskedPath: "../../etc/passwd" }),
    );
    expect(result).toMatchObject({ ok: false });
  });
});
