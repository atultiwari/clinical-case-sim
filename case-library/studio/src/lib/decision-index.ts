import type { Json } from "@/lib/ground-truth";
import { reviewTargetId, type ReviewTargetTable } from "@/lib/review-input";

/** The fields of a review_decision row the Studio shows beside each row. */
export type RowDecision = {
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

export type DecisionIndex = ReadonlyMap<string, readonly RowDecision[]>;

function key(targetTable: string, targetId: string): string {
  return `${targetTable}\u0000${targetId}`;
}

/** Decisions grouped by the row they are about, in the order given (newest first). */
export function indexDecisions(rows: readonly RowDecision[]): DecisionIndex {
  const index = new Map<string, RowDecision[]>();
  for (const row of rows) {
    const k = key(row.target_table, row.target_id);
    index.set(k, [...(index.get(k) ?? []), row]);
  }
  return index;
}

export function decisionsFor(
  index: DecisionIndex,
  targetTable: ReviewTargetTable,
  caseVersionId: string,
  rowId: string,
): readonly RowDecision[] {
  return index.get(key(targetTable, reviewTargetId(targetTable, caseVersionId, rowId))) ?? [];
}
