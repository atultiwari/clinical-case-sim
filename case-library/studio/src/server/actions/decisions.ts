"use server";

import { revalidatePath } from "next/cache";

import type { ActionState } from "@/lib/action-state";
import { caseHref } from "@/lib/case-id";
import { parseFigureDecision, parseReviewDecision } from "@/lib/review-input";
import { NotAllowedError, requireWriter } from "@/server/auth";
import { recordFigureDecision, recordReviewDecision, WriteRefusedError } from "@/server/writes";

const TABS = { synthetic_ledger: "ledger", report: "reports", consult_note: "reports", fact: "facts" } as const;

function failure(error: unknown, what: string): ActionState {
  if (error instanceof NotAllowedError || error instanceof WriteRefusedError) {
    return { ok: false, message: error.message };
  }
  // Log the cause for Atul (never the form values); show a plain message.
  const code = typeof error === "object" && error !== null && "code" in error ? String(error.code) : "";
  console.error(`Case Studio: ${what} failed`, code, error instanceof Error ? error.message : error);
  return { ok: false, message: `The ${what} was not saved. The server log has the details.` };
}

/** Records Approve, Edit or Reject for one row (ledger, report, consult note or fact). */
export async function submitReviewDecision(_previous: ActionState, form: FormData): Promise<ActionState> {
  try {
    const username = await requireWriter();
    const parsed = parseReviewDecision(form);
    if (!parsed.ok) return { ok: false, message: parsed.error };
    const recorded = await recordReviewDecision(parsed.value, username);
    revalidatePath(caseHref(parsed.value.caseVersionId, TABS[parsed.value.targetTable]));
    revalidatePath(caseHref(parsed.value.caseVersionId, "review"));
    return { ok: true, message: `Recorded (${parsed.value.decision}) in ${recorded.batchId}.` };
  } catch (error) {
    return failure(error, "review decision");
  }
}

/** Records use, mask or exclude for one figure. */
export async function submitFigureDecision(_previous: ActionState, form: FormData): Promise<ActionState> {
  try {
    const username = await requireWriter();
    const parsed = parseFigureDecision(form);
    if (!parsed.ok) return { ok: false, message: parsed.error };
    await recordFigureDecision(parsed.value, username);
    revalidatePath(caseHref(parsed.value.caseVersionId, "figures"));
    return { ok: true, message: `Recorded: ${parsed.value.decision}.` };
  } catch (error) {
    return failure(error, "figure decision");
  }
}
