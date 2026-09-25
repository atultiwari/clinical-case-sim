"use client";

import { useActionState, useState } from "react";

import type { ActionState } from "@/lib/action-state";
import { MAX_EDITED_LENGTH, MAX_NOTE_LENGTH, REVIEW_DECISIONS, type ReviewTargetTable } from "@/lib/review-input";
import { submitReviewDecision } from "@/server/actions/decisions";

type Props = {
  caseVersionId: string;
  targetTable: ReviewTargetTable;
  rowId: string;
  /** The current value, offered as the starting point for an edit. */
  currentValue?: string;
};

const LABELS = { approve: "Approve", edit: "Edit", reject: "Reject" } as const;

/** Approve, Edit (with the new value) or Reject one row (SPEC §7.2). */
export function ReviewDecisionForm({ caseVersionId, targetTable, rowId, currentValue }: Props) {
  const [state, action, pending] = useActionState<ActionState, FormData>(submitReviewDecision, null);
  const [decision, setDecision] = useState<(typeof REVIEW_DECISIONS)[number]>("approve");
  return (
    <details className="text-xs">
      <summary className="cursor-pointer select-none text-sky-800">Decide</summary>
      <form action={action} className="mt-1 space-y-1 rounded-md border bg-neutral-50 p-2">
        <input type="hidden" name="caseVersionId" value={caseVersionId} />
        <input type="hidden" name="targetTable" value={targetTable} />
        <input type="hidden" name="rowId" value={rowId} />
        <div className="flex flex-wrap gap-2">
          {REVIEW_DECISIONS.map((value) => (
            <label key={value} className="inline-flex items-center gap-1">
              <input
                type="radio"
                name="decision"
                value={value}
                checked={decision === value}
                onChange={() => setDecision(value)}
              />
              {LABELS[value]}
            </label>
          ))}
        </div>
        {decision === "edit" ? (
          <label className="block">
            <span className="text-muted-foreground">New value (JSON such as {"{\"value\": 80}"}, or text)</span>
            <textarea
              name="edited"
              required
              maxLength={MAX_EDITED_LENGTH}
              defaultValue={currentValue}
              rows={3}
              className="w-full rounded-md border bg-white px-1 py-0.5 font-mono"
            />
          </label>
        ) : null}
        <input
          name="note"
          maxLength={MAX_NOTE_LENGTH}
          placeholder="Note (optional)"
          className="w-full rounded-md border bg-white px-1 py-0.5"
        />
        <button type="submit" disabled={pending} className="rounded-md border bg-white px-2 py-0.5 hover:bg-muted disabled:opacity-50">
          {pending ? "Saving…" : "Record decision"}
        </button>
        {state ? (
          <p role="status" className={state.ok ? "text-emerald-800" : "text-red-700"}>
            {state.message}
          </p>
        ) : null}
      </form>
    </details>
  );
}
