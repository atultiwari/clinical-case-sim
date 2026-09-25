export const CASE_STATUSES = ["draft", "in_review", "frozen", "retired"] as const;
export type CaseStatus = (typeof CASE_STATUSES)[number];

export type Tone = "neutral" | "info" | "success" | "warning" | "danger" | "muted";

const STATUS_LABELS: Record<CaseStatus, string> = {
  draft: "Draft",
  in_review: "In review",
  frozen: "Frozen",
  retired: "Retired",
};

const STATUS_TONES: Record<CaseStatus, Tone> = {
  draft: "neutral",
  in_review: "warning",
  frozen: "info",
  retired: "muted",
};

function isCaseStatus(value: string): value is CaseStatus {
  return (CASE_STATUSES as readonly string[]).includes(value);
}

export function caseStatusLabel(status: string): string {
  return isCaseStatus(status) ? STATUS_LABELS[status] : status;
}

export function caseStatusTone(status: string): Tone {
  return isCaseStatus(status) ? STATUS_TONES[status] : "neutral";
}

/** Row review statuses (facts, ledger, reports, consult notes). */
export function reviewStatusTone(status: string): Tone {
  switch (status) {
    case "pending":
      return "warning";
    case "verified":
    case "approved":
      return "success";
    case "corrected":
    case "edited":
      return "info";
    case "rejected":
      return "danger";
    default:
      return "muted";
  }
}

/** 'in_review' becomes 'in review'; ids stay as they are otherwise. */
export function humanise(value: string): string {
  return value.replace(/_/g, " ");
}
