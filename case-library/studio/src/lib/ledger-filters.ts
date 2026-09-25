import { firstParam, oneOf, pageNumber, toQueryString, type SearchParams } from "@/lib/search-params";

export const LEDGER_TIERS = ["affected", "normal", "rule", "reviewer"] as const;
export const LEDGER_PRIORITIES = ["high", "medium", "low"] as const;
export const LEDGER_REVIEW_STATUSES = ["pending", "approved", "edited", "rejected", "superseded"] as const;
export const JUDGEMENT_OPTIONS = ["yes", "no"] as const;

export type LedgerFilters = {
  tier?: (typeof LEDGER_TIERS)[number];
  priority?: (typeof LEDGER_PRIORITIES)[number];
  status?: (typeof LEDGER_REVIEW_STATUSES)[number];
  judgement?: (typeof JUDGEMENT_OPTIONS)[number];
  target?: string;
  page: number;
};

export const LEDGER_PAGE_SIZE = 200;

/** Ledger filters from the page's search params; unknown values are ignored. */
export function parseLedgerFilters(params: SearchParams): LedgerFilters {
  const target = firstParam(params, "target");
  return {
    tier: oneOf(firstParam(params, "tier"), LEDGER_TIERS),
    priority: oneOf(firstParam(params, "priority"), LEDGER_PRIORITIES),
    status: oneOf(firstParam(params, "status"), LEDGER_REVIEW_STATUSES),
    judgement: oneOf(firstParam(params, "judgement"), JUDGEMENT_OPTIONS),
    target: target ? target.slice(0, 100) : undefined,
    page: pageNumber(firstParam(params, "page")),
  };
}

/** judgement=yes|no as the boolean the query compares with (null = any). */
export function judgementValue(filters: LedgerFilters): boolean | null {
  if (filters.judgement === "yes") return true;
  if (filters.judgement === "no") return false;
  return null;
}

/** The query string for these filters with some changed; a change resets the page. */
export function ledgerQuery(filters: LedgerFilters, change: Partial<LedgerFilters>): string {
  const next = { ...filters, page: 1, ...change };
  return toQueryString({
    tier: next.tier,
    priority: next.priority,
    status: next.status,
    judgement: next.judgement,
    target: next.target,
    page: next.page > 1 ? next.page : undefined,
  });
}

export function hasActiveFilters(filters: LedgerFilters): boolean {
  return Boolean(filters.tier || filters.priority || filters.status || filters.judgement || filters.target);
}
