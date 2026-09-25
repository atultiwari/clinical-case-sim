import "server-only";

import type { Json } from "@/lib/ground-truth";
import { withReader } from "@/server/db";

export type ReviewBatchRow = {
  id: string;
  case_version_ids: string[];
  pack_path: string | null;
  created_at: Date;
  returned_at: Date | null;
  applied_at: Date | null;
  decisions: number;
};

export type ReviewDecisionRow = {
  id: string;
  batch_id: string;
  target_table: string;
  target_id: string;
  decision: string;
  edited: Json | null;
  note: string | null;
  decided_by: string;
  decided_at: Date;
};

export type SupersededRow = {
  id: string;
  target: string;
  day_bucket: number | null;
  tier: string;
  value: Json;
  review_note: string | null;
  replaced_by: string | null;
  created_at: Date;
};

export const DECISION_LIMIT = 1000;

export async function listReviewBatches(caseVersionId: string): Promise<ReviewBatchRow[]> {
  return withReader((sql) => sql<ReviewBatchRow[]>`
    select b.id, b.case_version_ids, b.pack_path, b.created_at, b.returned_at, b.applied_at,
           (select count(*)::int from casevault.review_decision d where d.batch_id = b.id) as decisions
    from casevault.review_batch b
    where ${caseVersionId}::text = any (b.case_version_ids)
    order by b.created_at desc
  `);
}

/**
 * Decisions about this case version: from its batches, keyed '<case version>/…',
 * a ledger row of this version, or any row of a batch that holds only this version.
 */
export async function listReviewDecisions(caseVersionId: string): Promise<ReviewDecisionRow[]> {
  return withReader((sql) => sql<ReviewDecisionRow[]>`
    select d.id::text as id, d.batch_id, d.target_table, d.target_id, d.decision, d.edited, d.note,
           d.decided_by, d.decided_at
    from casevault.review_decision d
    join casevault.review_batch b on b.id = d.batch_id
    where ${caseVersionId}::text = any (b.case_version_ids)
      and (cardinality(b.case_version_ids) = 1
           or d.target_id = ${caseVersionId}::text
           or starts_with(d.target_id, ${caseVersionId}::text || '/')
           or exists (select 1 from casevault.synthetic_ledger l
                      where l.id::text = d.target_id and l.case_version_id = ${caseVersionId}::text))
    order by d.decided_at desc, d.id desc
    limit ${DECISION_LIMIT}
  `);
}

export async function listSupersededLedger(caseVersionId: string): Promise<SupersededRow[]> {
  return withReader((sql) => sql<SupersededRow[]>`
    select l.id::text as id, l.target, l.day_bucket, l.tier, l.value, l.review_note,
           (select n.id::text from casevault.synthetic_ledger n where n.supersedes = l.id limit 1) as replaced_by,
           l.created_at
    from casevault.synthetic_ledger l
    where l.case_version_id = ${caseVersionId} and l.review_status = 'superseded'
    order by l.target, l.day_bucket nulls first, l.created_at
  `);
}
