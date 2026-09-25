/**
 * Integration tests against a real Case Vault (the local database). Skipped
 * unless CASE_VAULT_DB_URL_READONLY is set. They only read: the write checks
 * expect the database to refuse.
 */
import { afterAll, describe, expect, it } from "vitest";

import { parseCatalogueParams } from "@/lib/catalogue-params";
import { parseLedgerFilters } from "@/lib/ledger-filters";
import { closeDb, withReader } from "@/server/db";
import { getCaseOverview, listBundles, listCaseVersions } from "@/server/queries/cases";
import { listCatalogueItems, listComponents } from "@/server/queries/catalogue";
import { listFacts } from "@/server/queries/facts";
import { getGroundTruth, listTestUtility } from "@/server/queries/ground-truth";
import { listLedger } from "@/server/queries/ledger";
import { listMedia } from "@/server/queries/media";
import { listMissingRequests } from "@/server/queries/missing-requests";
import { coverageReport, listCoverageGaps, listGapGuidance, listPaths } from "@/server/queries/paths";
import { listConsultNotes, listReports } from "@/server/queries/reports";
import { listReviewBatches, listReviewDecisions, listSupersededLedger } from "@/server/queries/review";

const hasDatabase = Boolean(process.env.CASE_VAULT_DB_URL_READONLY);
const READ_ONLY_OR_DENIED = /read-only transaction|permission denied/i;

describe.skipIf(!hasDatabase)("Case Studio queries (local Case Vault)", () => {
  afterAll(async () => {
    await closeDb();
  });

  it("reads as casevault_reader in a read-only transaction", async () => {
    const [row] = await withReader((sql) => sql<{ role: string; read_only: string }[]>`
      select current_user as role, current_setting('transaction_read_only') as read_only
    `);
    expect(row).toEqual({ role: "casevault_reader", read_only: "on" });
  });

  it("refuses an insert through the same connection", async () => {
    await expect(
      withReader((sql) => sql`
        insert into casevault.missing_request (source, query) values ('nidana', 'studio write test')
      `),
    ).rejects.toThrow(READ_ONLY_OR_DENIED);
  });

  it("refuses to switch the transaction to read-write or reset the role and write", async () => {
    await expect(
      withReader(async (sql) => {
        await sql`reset role`;
        await sql`insert into casevault.missing_request (source, query) values ('nidana', 'studio write test')`;
      }),
    ).rejects.toThrow(READ_ONLY_OR_DENIED);
  });

  it("refuses the writing Case Vault functions", async () => {
    await expect(
      withReader((sql) => sql`select casevault.resolve_normals('PMC1@v1')`),
    ).rejects.toThrow(READ_ONLY_OR_DENIED);
  });

  it("lists case versions, empty or not", async () => {
    const cases = await listCaseVersions();
    expect(Array.isArray(cases)).toBe(true);
    for (const row of cases) {
      expect(row.id).toMatch(/@v\d+$/);
      expect(typeof row.coverage_total).toBe("number");
      expect(row.coverage_resolved).toBeLessThanOrEqual(row.coverage_total);
      expect(typeof row.open_review).toBe("number");
      expect(typeof row.fact_origins).toBe("object");
    }
  });

  it("returns null for a case version that does not exist", async () => {
    expect(await getCaseOverview("PMC1@v999")).toBeNull();
  });

  it("reads every tab of the first case version (or an empty one)", async () => {
    const cases = await listCaseVersions();
    const id = cases[0]?.id ?? "PMC1@v999";
    const [facts, ledger, reports, notes, media, gt, utility, paths, report, gaps, guidance, batches, decisions, superseded, bundles] =
      await Promise.all([
        listFacts(id),
        listLedger(id, parseLedgerFilters({ tier: "normal", judgement: "no", target: "CMP" })),
        listReports(id),
        listConsultNotes(id),
        listMedia(id),
        getGroundTruth(id),
        listTestUtility(id),
        listPaths(id),
        coverageReport(id),
        listCoverageGaps(id),
        listGapGuidance(id),
        listReviewBatches(id),
        listReviewDecisions(id),
        listSupersededLedger(id),
        listBundles(id),
      ]);
    expect(ledger.total).toBeGreaterThanOrEqual(ledger.rows.length);
    for (const row of ledger.rows) expect(row.tier).toBe("normal");
    for (const fact of facts) expect(["article", "derived"]).toContain(fact.origin);
    expect([reports, notes, media, utility, paths, report, gaps, guidance, batches, decisions, superseded, bundles].every(Array.isArray)).toBe(true);
    if (cases.length === 0) expect(gt).toBeNull();
  });

  it("pages and searches the catalogue", async () => {
    const items = await listCatalogueItems(parseCatalogueParams({ kind: "test", q: "blood" }));
    expect(items.rows.length).toBeLessThanOrEqual(50);
    for (const item of items.rows) expect(item.kind).toBe("test");
    const components = await listComponents(parseCatalogueParams({ view: "components", q: "%" }));
    expect(components.total).toBeGreaterThanOrEqual(0);
  });

  it("groups missing requests", async () => {
    const groups = await listMissingRequests();
    for (const group of groups) expect(group.frequency).toBeGreaterThan(0);
  });
});
