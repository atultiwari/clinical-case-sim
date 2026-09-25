import type { SeriesPoint } from "@/lib/types";

export type SparklineGeometry = {
  path: string;
  dots: { x: number; y: number; day: number; value: number; flag: string | null }[];
  min: number;
  max: number;
};

export type SparklineSize = { width: number; height: number; padding: number };

export const DEFAULT_SPARKLINE_SIZE: SparklineSize = { width: 120, height: 28, padding: 3 };

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

/**
 * An SVG path for serial values: x by day (so gaps between days show), y by
 * value, scaled to the series' own range. A flat series is drawn mid-height.
 */
export function sparkline(
  points: readonly SeriesPoint[],
  size: SparklineSize = DEFAULT_SPARKLINE_SIZE,
): SparklineGeometry | null {
  if (points.length === 0) return null;
  const sorted = [...points].sort((a, b) => a.day - b.day);
  const values = sorted.map((point) => point.value);
  const days = sorted.map((point) => point.day);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const firstDay = Math.min(...days);
  const daySpan = Math.max(...days) - firstDay;
  const innerWidth = size.width - size.padding * 2;
  const innerHeight = size.height - size.padding * 2;

  const dots = sorted.map((point) => {
    const x = daySpan === 0 ? size.width / 2 : size.padding + ((point.day - firstDay) / daySpan) * innerWidth;
    const y = max === min
      ? size.height / 2
      : size.padding + (1 - (point.value - min) / (max - min)) * innerHeight;
    return { x: round(x), y: round(y), day: point.day, value: point.value, flag: point.flag };
  });

  const path = dots.map((dot, index) => `${index === 0 ? "M" : "L"}${dot.x} ${dot.y}`).join(" ");
  return { path, dots, min, max };
}
