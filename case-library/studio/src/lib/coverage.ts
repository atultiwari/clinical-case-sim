/** One row of casevault.coverage_report(case version). */
export type CoverageRow = { kind: string; total: number; resolved: number; missing: string[] };

export type CoverageSummary = { resolved: number; total: number; percent: number | null };

/** Resolved of total, with the share rounded down to one decimal (never shows 100% early). */
export function coverageOf(resolved: number, total: number): CoverageSummary {
  return { resolved, total, percent: total === 0 ? null : Math.floor((resolved / total) * 1000) / 10 };
}

export function summariseCoverage(rows: readonly CoverageRow[]): CoverageSummary {
  const total = rows.reduce((sum, row) => sum + row.total, 0);
  const resolved = rows.reduce((sum, row) => sum + row.resolved, 0);
  return coverageOf(resolved, total);
}

export function formatCoverage(summary: CoverageSummary): string {
  if (summary.total === 0) return "no active items";
  return `${summary.resolved}/${summary.total} (${summary.percent}%)`;
}

/** Coverage gaps (casevault.coverage_gaps) grouped by catalogue item. */
export type CoverageGap = { kind: string; item_id: string; component_id: string | null; day: number | null };
export type GapGroup = { kind: string; itemId: string; components: { componentId: string; days: number[] }[] };

export function groupCoverageGaps(gaps: readonly CoverageGap[]): GapGroup[] {
  const byItem = new Map<string, { kind: string; components: Map<string, number[]> }>();
  for (const gap of gaps) {
    const entry = byItem.get(gap.item_id) ?? { kind: gap.kind, components: new Map<string, number[]>() };
    if (gap.component_id !== null) {
      const days = entry.components.get(gap.component_id) ?? [];
      entry.components.set(gap.component_id, gap.day === null ? days : [...days, gap.day]);
    }
    byItem.set(gap.item_id, entry);
  }
  return [...byItem.entries()].map(([itemId, entry]) => ({
    kind: entry.kind,
    itemId,
    components: [...entry.components.entries()].map(([componentId, days]) => ({
      componentId,
      days: [...days].sort((a, b) => a - b),
    })),
  }));
}
