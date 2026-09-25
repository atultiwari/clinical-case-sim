import type { FactRow, SeriesPoint } from "@/lib/types";

export type FactItemGroup = {
  key: string;
  label: string;
  unit: string | null;
  rows: FactRow[];
  /** Numeric values on two or more days, in day order: drawn as a sparkline. */
  series: SeriesPoint[] | null;
};

export type FactCategoryGroup = { category: string; items: FactItemGroup[] };

function seriesOf(rows: readonly FactRow[]): SeriesPoint[] | null {
  const points = rows
    .filter((row): row is FactRow & { day: number; value_num: number } =>
      row.day !== null && row.value_num !== null && Number.isFinite(row.value_num))
    .map((row) => ({ day: row.day, value: row.value_num, flag: row.flag }))
    .sort((a, b) => a.day - b.day);
  const days = new Set(points.map((point) => point.day));
  return days.size >= 2 ? points : null;
}

function byDay(a: FactRow, b: FactRow): number {
  return (a.day ?? -1) - (b.day ?? -1) || a.id.localeCompare(b.id);
}

/**
 * Facts grouped by category, then by item (catalogue id, or the item name when
 * there is none). Categories and items keep the order in which they first appear.
 */
export function groupFacts(facts: readonly FactRow[]): FactCategoryGroup[] {
  const categories = new Map<string, Map<string, FactRow[]>>();
  for (const fact of facts) {
    const items = categories.get(fact.category) ?? new Map<string, FactRow[]>();
    const key = fact.catalogue_ref ?? `item:${fact.item}`;
    items.set(key, [...(items.get(key) ?? []), fact]);
    categories.set(fact.category, items);
  }
  return [...categories.entries()].map(([category, items]) => ({
    category,
    items: [...items.entries()].map(([key, rows]) => {
      const sorted = [...rows].sort(byDay);
      const first = sorted[0];
      return {
        key,
        label: first?.item ?? key,
        unit: sorted.find((row) => row.unit)?.unit ?? null,
        rows: sorted,
        series: seriesOf(sorted),
      };
    }),
  }));
}
