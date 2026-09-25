import { OriginBadge, ReviewBadge } from "@/components/badges";
import { Empty, FilterLinks, Pager, type FilterOption } from "@/components/common";
import { ReviewNotice, RowReview } from "@/components/review/row-review";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { caseHref } from "@/lib/case-id";
import { pageCount } from "@/lib/catalogue-params";
import { formatDay } from "@/lib/format";
import { prettyJson } from "@/lib/ground-truth";
import {
  hasActiveFilters,
  JUDGEMENT_OPTIONS,
  LEDGER_PAGE_SIZE,
  LEDGER_PRIORITIES,
  LEDGER_REVIEW_STATUSES,
  LEDGER_TIERS,
  ledgerQuery,
  parseLedgerFilters,
  type LedgerFilters,
} from "@/lib/ledger-filters";
import type { SearchParams } from "@/lib/search-params";
import { loadCase, type CaseParams } from "@/server/case-page";
import { listLedger } from "@/server/queries/ledger";
import { loadReviewContext } from "@/server/review-context";

type Props = { params: CaseParams; searchParams: Promise<SearchParams> };

function options<K extends "tier" | "priority" | "status" | "judgement">(
  base: string,
  filters: LedgerFilters,
  key: K,
  values: readonly NonNullable<LedgerFilters[K]>[],
  counts: Record<string, number> = {},
): FilterOption[] {
  return [
    { label: "any", href: base + ledgerQuery(filters, { [key]: undefined }), active: !filters[key] },
    ...values.map((value) => ({
      label: value,
      href: base + ledgerQuery(filters, { [key]: value }),
      active: filters[key] === value,
      count: counts[value],
    })),
  ];
}

export default async function LedgerPage({ params, searchParams }: Props) {
  const c = await loadCase(params);
  const filters = parseLedgerFilters(await searchParams);
  const [{ rows, total, facets }, review] = await Promise.all([
    listLedger(c.id, filters),
    loadReviewContext(c.id, c.status),
  ]);
  const base = caseHref(c.id, "ledger");
  return (
    <>
      <div className="mb-3 space-y-1">
        <FilterLinks label="Tier" options={options(base, filters, "tier", LEDGER_TIERS, facets.tiers)} />
        <FilterLinks label="Priority" options={options(base, filters, "priority", LEDGER_PRIORITIES)} />
        <FilterLinks label="Judgement call" options={options(base, filters, "judgement", JUDGEMENT_OPTIONS)} />
        <FilterLinks label="Review status" options={options(base, filters, "status", LEDGER_REVIEW_STATUSES, facets.statuses)} />
        <form action={base} className="flex items-center gap-1">
          <span className="w-28 text-xs text-muted-foreground">Target</span>
          {(["tier", "priority", "status", "judgement"] as const).map((key) =>
            filters[key] ? <input key={key} type="hidden" name={key} value={filters[key]} /> : null,
          )}
          <input name="target" defaultValue={filters.target} placeholder="id or name" className="rounded-md border px-2 py-0.5 text-xs" />
          <button type="submit" className="rounded-md border px-2 py-0.5 text-xs hover:bg-muted">Filter</button>
          {hasActiveFilters(filters) ? <a href={base} className="text-xs">Clear all</a> : null}
        </form>
      </div>
      <ReviewNotice canWrite={review.context.canWrite} reason={review.notice} />
      <p className="mb-2 text-xs text-muted-foreground">{total} rows</p>
      {rows.length === 0 ? (
        <Empty>No ledger rows{hasActiveFilters(filters) ? " match these filters" : " yet"}.</Empty>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Target</TableHead>
              <TableHead>Day</TableHead>
              <TableHead>Tier</TableHead>
              <TableHead>Value</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Review</TableHead>
              <TableHead>Rationale</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id}>
                <TableCell>
                  <div className="font-mono text-xs">{row.target}</div>
                  {row.target_name ? <div className="text-xs text-muted-foreground">{row.target_name}</div> : null}
                </TableCell>
                <TableCell className="whitespace-nowrap">{formatDay(row.day_bucket)}</TableCell>
                <TableCell>
                  <OriginBadge origin={row.tier} />
                  {row.judgement_call ? <Badge tone="warning" className="ml-1">judgement call</Badge> : null}
                </TableCell>
                <TableCell className="max-w-md">
                  <code className="text-xs break-all">{prettyJson(row.value)}</code>
                  {row.release_text ? <div className="text-xs">{row.release_text}</div> : null}
                </TableCell>
                <TableCell>{row.priority ?? "—"}</TableCell>
                <TableCell className="min-w-48">
                  <ReviewBadge status={row.review_status} />
                  {row.review_note ? <div className="text-xs">{row.review_note}</div> : null}
                  <RowReview
                    context={review.context}
                    targetTable="synthetic_ledger"
                    rowId={row.id}
                    currentValue={prettyJson(row.value)}
                  />
                </TableCell>
                <TableCell className="max-w-sm text-xs">
                  {row.rationale ?? "—"}
                  {row.confidence !== null ? <span className="text-muted-foreground"> (confidence {row.confidence})</span> : null}
                  <div className="font-mono text-muted-foreground">{row.generator}</div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      <Pager
        page={filters.page}
        pages={pageCount(total, LEDGER_PAGE_SIZE)}
        href={(page) => base + ledgerQuery(filters, { page })}
      />
    </>
  );
}
