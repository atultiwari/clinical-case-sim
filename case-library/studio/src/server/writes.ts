import "server-only";

import {
  reviewTargetId,
  studioBatchId,
  type FigureDecisionInput,
  type ReviewDecisionInput,
  type ReviewTargetTable,
} from "@/lib/review-input";
import { withWriter, type Writer } from "@/server/writer-db";

/** A refusal whose message is safe to show in the Studio. */
export class WriteRefusedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WriteRefusedError";
  }
}

const REVIEWABLE_STATUSES = new Set(["draft", "in_review"]);

async function caseVersionStatus(sql: Writer, caseVersionId: string): Promise<string> {
  const [row] = await sql<{ status: string }[]>`
    select status from casevault.case_version where id = ${caseVersionId}
  `;
  if (!row) throw new WriteRefusedError("Unknown case version.");
  return row.status;
}

async function rowExists(sql: Writer, table: ReviewTargetTable, caseVersionId: string, rowId: string): Promise<boolean> {
  // One fixed statement per table: no identifier is ever built from input.
  switch (table) {
    case "synthetic_ledger":
      return (
        (await sql`select 1 from casevault.synthetic_ledger where id = ${rowId}::uuid and case_version_id = ${caseVersionId}`)
          .length > 0
      );
    case "report":
      return (await sql`select 1 from casevault.report where case_version_id = ${caseVersionId} and id = ${rowId}`).length > 0;
    case "consult_note":
      return (
        (await sql`select 1 from casevault.consult_note where case_version_id = ${caseVersionId} and id = ${rowId}`).length > 0
      );
    case "fact":
      return (await sql`select 1 from casevault.fact where case_version_id = ${caseVersionId} and id = ${rowId}`).length > 0;
  }
}

function batchSequence(base: string, id: string): number {
  if (id === base) return 1;
  const suffix = id.slice(base.length + 1);
  return /^[0-9]{1,4}$/.test(suffix) ? Number(suffix) : 0;
}

/**
 * Today's open Studio batch for this user, holding this case version: created on
 * the day's first decision; a new one ('-2', '-3', …) once Claude has applied it.
 */
async function openStudioBatch(sql: Writer, username: string, caseVersionId: string, now: Date): Promise<string> {
  const base = studioBatchId(now, username);
  const batches = await sql<{ id: string; case_version_ids: string[]; applied: boolean }[]>`
    select id, case_version_ids, applied_at is not null as applied
    from casevault.review_batch
    where id = ${base} or starts_with(id, ${`${base}-`})
  `;
  const known = batches
    .map((batch) => ({ ...batch, sequence: batchSequence(base, batch.id) }))
    .filter((batch) => batch.sequence > 0)
    .sort((a, b) => b.sequence - a.sequence);

  const open = known.find((batch) => !batch.applied);
  if (open) {
    if (!open.case_version_ids.includes(caseVersionId)) {
      await sql`
        update casevault.review_batch
        set case_version_ids = array_append(case_version_ids, ${caseVersionId}::text)
        where id = ${open.id} and applied_at is null
      `;
    }
    return open.id;
  }

  const id = studioBatchId(now, username, (known[0]?.sequence ?? 0) + 1);
  const inserted = await sql`
    insert into casevault.review_batch (id, case_version_ids)
    values (${id}, ${[caseVersionId]}::text[])
    on conflict (id) do nothing
    returning id
  `;
  if (inserted.length === 0) throw new WriteRefusedError("Another decision was being saved at the same time. Try again.");
  return id;
}

export type RecordedDecision = { id: string; batchId: string };

/** Records one review decision (SPEC §7.2). Claude applies it to the content later (§7.3). */
export async function recordReviewDecision(
  input: ReviewDecisionInput,
  username: string,
  now: Date = new Date(),
): Promise<RecordedDecision> {
  return withWriter(async (sql) => {
    const status = await caseVersionStatus(sql, input.caseVersionId);
    if (!REVIEWABLE_STATUSES.has(status)) {
      throw new WriteRefusedError(`This case version is ${status}; review decisions apply only to drafts and versions in review.`);
    }
    if (!(await rowExists(sql, input.targetTable, input.caseVersionId, input.rowId))) {
      throw new WriteRefusedError("That row is not part of this case version.");
    }
    const batchId = await openStudioBatch(sql, username, input.caseVersionId, now);
    // sql.json sends the value as one jsonb parameter (a string cast with ::jsonb would be encoded twice).
    const edited = input.edited === null ? null : sql.json(input.edited);
    const [row] = await sql<{ id: string }[]>`
      insert into casevault.review_decision
        (batch_id, target_table, target_id, decision, edited, note, decided_by)
      values
        (${batchId}, ${input.targetTable}, ${reviewTargetId(input.targetTable, input.caseVersionId, input.rowId)},
         ${input.decision}, ${edited}, ${input.note}, ${username})
      returning id::text as id
    `;
    if (!row) throw new Error("The review decision was not recorded");
    return { id: row.id, batchId };
  });
}

/** Records a figure's production decision (SPEC §9); allowed after freeze, never once retired. */
export async function recordFigureDecision(input: FigureDecisionInput, username: string): Promise<void> {
  await withWriter(async (sql) => {
    const status = await caseVersionStatus(sql, input.caseVersionId);
    if (status === "retired") throw new WriteRefusedError("This case version is retired; its figures cannot change.");
    const updated = await sql`
      update casevault.media
      set production_decision = ${input.decision},
          masked_path = ${input.maskedPath},
          decided_by = ${username},
          decided_at = now()
      where case_version_id = ${input.caseVersionId} and id = ${input.mediaId}
      returning id
    `;
    if (updated.length === 0) throw new WriteRefusedError("That figure is not part of this case version.");
  });
}
