import "server-only";

import { containsPattern } from "@/lib/catalogue-params";
import type { Json } from "@/lib/ground-truth";
import { judgementValue, LEDGER_PAGE_SIZE, type LedgerFilters } from "@/lib/ledger-filters";
import { withReader } from "@/server/db";

export type LedgerRow = {
  id: string;
  target: string;
  target_name: string | null;
  day_bucket: number | null;
  tier: string;
  gap_id: string | null;
  value: Json;
  release_text: string | null;
  priority: string | null;
  judgement_call: boolean;
  generator: string;
  rationale: string | null;
  confidence: number | null;
  review_status: string;
  reviewed_by: string | null;
  review_note: string | null;
  supersedes: string | null;
  created_at: Date;
};

export type LedgerFacets = { tiers: Record<string, number>; statuses: Record<string, number> };
export type LedgerPage = { rows: LedgerRow[]; total: number; facets: LedgerFacets };

/** Ledger rows for one case version, filtered and paged in the database. */
export async function listLedger(caseVersionId: string, filters: LedgerFilters): Promise<LedgerPage> {
  const tier = filters.tier ?? null;
  const priority = filters.priority ?? null;
  const status = filters.status ?? null;
  const judgement = judgementValue(filters);
  const target = filters.target ? containsPattern(filters.target) : null;
  const offset = (filters.page - 1) * LEDGER_PAGE_SIZE;

  return withReader(async (sql) => {
    const matching = sql`
      from casevault.synthetic_ledger l
      left join casevault.component cmp on cmp.id = l.target
      left join casevault.catalogue_item ci on ci.id = l.target
      where l.case_version_id = ${caseVersionId}
        and (${tier}::text is null or l.tier = ${tier}::text)
        and (${priority}::text is null or l.priority = ${priority}::text)
        and (${status}::text is null or l.review_status = ${status}::text)
        and (${judgement}::boolean is null or l.judgement_call = ${judgement}::boolean)
        and (${target}::text is null or l.target ilike ${target}::text
             or coalesce(cmp.name, ci.name, '') ilike ${target}::text)
    `;
    const rows = await sql<LedgerRow[]>`
      select l.id::text as id, l.target, coalesce(cmp.name, ci.name) as target_name, l.day_bucket,
             l.tier, l.gap_id, l.value, l.release_text, l.priority, l.judgement_call, l.generator,
             l.rationale, l.confidence::float8 as confidence, l.review_status, l.reviewed_by,
             l.review_note, l.supersedes::text as supersedes, l.created_at
      ${matching}
      order by l.target, l.day_bucket nulls first, l.created_at
      limit ${LEDGER_PAGE_SIZE} offset ${offset}
    `;
    const [count] = await sql<{ total: number }[]>`select count(*)::int as total ${matching}`;
    const [facets] = await sql<LedgerFacets[]>`
      select
        (select coalesce(jsonb_object_agg(x.tier, x.n), '{}'::jsonb) from (
           select tier, count(*)::int as n from casevault.synthetic_ledger
           where case_version_id = ${caseVersionId} group by tier) x) as tiers,
        (select coalesce(jsonb_object_agg(x.review_status, x.n), '{}'::jsonb) from (
           select review_status, count(*)::int as n from casevault.synthetic_ledger
           where case_version_id = ${caseVersionId} group by review_status) x) as statuses
    `;
    return {
      rows,
      total: count?.total ?? 0,
      facets: facets ?? { tiers: {}, statuses: {} },
    };
  });
}
