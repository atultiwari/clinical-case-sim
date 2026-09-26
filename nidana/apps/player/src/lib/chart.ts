import type { ChartEntry, ResultValue } from "@nidana/contracts/api";

/** How the Chart is arranged for reading (SPEC §5.3): by day, results as tables, serial values as trends. */

export type Units = "si" | "conventional";

export interface DisplayValue {
  readonly text: string;
  readonly unit: string | null;
  readonly refRange: string | null;
  readonly flag: string | null;
}

/** Shows a result in SI as stored, or converted (conventional = SI × factor), keeping the laboratory's flag. */
export function displayValue(value: ResultValue, units: Units): DisplayValue {
  const numeric = Number(value.value);
  const conv = value.conventional;
  if (
    units === "conventional" &&
    conv !== null &&
    value.value.trim() !== "" &&
    Number.isFinite(numeric)
  ) {
    const converted = numeric * conv.factor;
    const text =
      conv.decimals === null
        ? String(Number(converted.toPrecision(4)))
        : converted.toFixed(conv.decimals);
    return {
      text,
      unit: conv.unit,
      refRange: convertRange(value.refRange, conv.factor, conv.decimals),
      flag: value.flag,
    };
  }
  return {
    text: value.value,
    unit: value.unit,
    refRange: value.refRange,
    flag: value.flag,
  };
}

function convertRange(
  range: string | null,
  factor: number,
  decimals: number | null,
): string | null {
  if (range === null) return null;
  const match = /^\s*(-?[\d.]+)\s*[-–]\s*(-?[\d.]+)\s*$/.exec(range);
  if (match === null) return null;
  const fmt = (n: number): string =>
    decimals === null ? String(Number(n.toPrecision(4))) : n.toFixed(decimals);
  return `${fmt(Number(match[1]) * factor)}–${fmt(Number(match[2]) * factor)}`;
}

export interface ResultRow {
  readonly entry: ChartEntry;
  readonly name: string;
}

export interface ResultTable {
  /** The test that was ordered, and when its results arrived. */
  readonly item: string;
  readonly itemName: string;
  readonly at: number;
  readonly requestedDay: number | null;
  readonly rows: readonly ResultRow[];
}

export type ChartBlock =
  | { readonly type: "entry"; readonly entry: ChartEntry }
  | { readonly type: "results"; readonly table: ResultTable };

/** Groups consecutive result entries from one order into a table; everything else stays one block per entry. */
export function chartBlocks(entries: readonly ChartEntry[]): ChartBlock[] {
  const blocks: ChartBlock[] = [];
  for (const entry of entries) {
    if (entry.kind !== "result" || entry.component === null) {
      blocks.push({ type: "entry", entry });
      continue;
    }
    const last = blocks.at(-1);
    const row = { entry, name: entry.component.name };
    if (
      last?.type === "results" &&
      last.table.item === entry.item &&
      last.table.at === entry.at
    ) {
      blocks[blocks.length - 1] = {
        type: "results",
        table: { ...last.table, rows: [...last.table.rows, row] },
      };
    } else {
      blocks.push({
        type: "results",
        table: {
          item: entry.item ?? "",
          itemName: entry.itemName ?? entry.item ?? "Result",
          at: entry.at,
          requestedDay: entry.requestedDay,
          rows: [row],
        },
      });
    }
  }
  return blocks;
}

/** Days of the Chart, each with its blocks, in time order. */
export function blocksByDay(
  entries: readonly ChartEntry[],
): { day: number; blocks: ChartBlock[] }[] {
  const days = new Map<number, ChartEntry[]>();
  for (const entry of entries) {
    const day = Math.floor(entry.at / 1440);
    days.set(day, [...(days.get(day) ?? []), entry]);
  }
  return [...days.entries()]
    .sort(([a], [b]) => a - b)
    .map(([day, list]) => ({ day, blocks: chartBlocks(list) }));
}

export interface TrendPoint {
  readonly day: number;
  readonly value: number;
  readonly flag: string | null;
}

/** The serial values of one component, one per day asked for (the latest release wins), for trend lines. */
export function trendOf(
  entries: readonly ChartEntry[],
  component: string,
): TrendPoint[] {
  const byDay = new Map<number, TrendPoint>();
  for (const entry of entries) {
    if (entry.component?.id !== component || entry.value === null) continue;
    const value = Number(entry.value.value);
    const day = entry.takenDay ?? entry.requestedDay;
    if (!Number.isFinite(value) || day === null) continue;
    byDay.set(day, { day, value, flag: entry.value.flag });
  }
  return [...byDay.values()].sort((a, b) => a.day - b.day);
}

/** "Result from day 0", when a value was carried forward to a later order (changelog 2026-09-25). */
export function carriedLabel(entry: ChartEntry): string | null {
  return entry.takenDay === null ? null : `Result from day ${entry.takenDay}`;
}
