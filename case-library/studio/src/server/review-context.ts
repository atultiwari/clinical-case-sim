import "server-only";

import type { RowReviewContext } from "@/components/review/row-review";
import { indexDecisions } from "@/lib/decision-index";
import { currentUser, writeAvailability } from "@/server/auth";
import { listReviewDecisions } from "@/server/queries/review";

export type ReviewPageContext = { context: RowReviewContext; notice?: string };

/** Whether this request may record decisions; the actions check again on the server. */
export async function canRecord(): Promise<{ allowed: boolean; reason?: string }> {
  const availability = writeAvailability();
  if (!availability.enabled) return { allowed: false, reason: availability.reason };
  return (await currentUser()) ? { allowed: true } : { allowed: false, reason: "Log in to record decisions." };
}

/** Earlier decisions for a case version, and whether review decisions can be recorded on it. */
export async function loadReviewContext(caseVersionId: string, status: string): Promise<ReviewPageContext> {
  const [decisions, permission] = await Promise.all([listReviewDecisions(caseVersionId), canRecord()]);
  const reviewable = status === "draft" || status === "in_review";
  const canWrite = permission.allowed && reviewable;
  const notice = permission.allowed
    ? reviewable
      ? undefined
      : `This case version is ${status.replace("_", " ")}: review decisions apply only to drafts and versions in review.`
    : permission.reason;
  return { context: { caseVersionId, decisions: indexDecisions(decisions), canWrite }, notice };
}
