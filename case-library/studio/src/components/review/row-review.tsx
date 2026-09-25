import { ReviewDecisionForm } from "@/components/review/review-decision-form";
import { Badge } from "@/components/ui/badge";
import { decisionsFor, type DecisionIndex } from "@/lib/decision-index";
import { formatDateTime } from "@/lib/format";
import { prettyJson } from "@/lib/ground-truth";
import type { ReviewTargetTable } from "@/lib/review-input";

const TONES = { approve: "success", edit: "info", reject: "danger" } as const;

export type RowReviewContext = { caseVersionId: string; decisions: DecisionIndex; canWrite: boolean };

/** Earlier decisions about one row, and (when the Studio can write) the form for a new one. */
export function RowReview({
  context,
  targetTable,
  rowId,
  currentValue,
}: {
  context: RowReviewContext;
  targetTable: ReviewTargetTable;
  rowId: string;
  currentValue?: string;
}) {
  const decisions = decisionsFor(context.decisions, targetTable, context.caseVersionId, rowId);
  return (
    <div className="mt-1 space-y-1">
      {decisions.length > 0 ? (
        <ul className="space-y-0.5 text-xs">
          {decisions.map((d) => (
            <li key={d.id} title={`Batch ${d.batch_id}`}>
              <Badge tone={TONES[d.decision as keyof typeof TONES] ?? "neutral"}>{d.decision}</Badge>{" "}
              <span className="text-muted-foreground">
                {d.decided_by}, {formatDateTime(d.decided_at)}
              </span>
              {d.edited !== null ? <code className="ml-1 break-all">{prettyJson(d.edited)}</code> : null}
              {d.note ? <span className="ml-1 italic">{d.note}</span> : null}
            </li>
          ))}
        </ul>
      ) : null}
      {context.canWrite ? (
        <ReviewDecisionForm
          caseVersionId={context.caseVersionId}
          targetTable={targetTable}
          rowId={rowId}
          currentValue={currentValue}
        />
      ) : null}
    </div>
  );
}

/** Says what recording a decision does, or why the Studio cannot. */
export function ReviewNotice({ canWrite, reason }: { canWrite: boolean; reason?: string }) {
  return canWrite ? (
    <p className="mb-2 rounded-md border border-sky-200 bg-sky-50 p-2 text-xs text-sky-900">
      Decisions made here are recorded in <code>review_decision</code> under today&apos;s Studio batch. They do not change the
      content: Claude applies them through the MCP after your go-ahead (SPEC §7.3).
    </p>
  ) : reason ? (
    <p className="mb-2 text-xs text-muted-foreground">{reason}</p>
  ) : null;
}
