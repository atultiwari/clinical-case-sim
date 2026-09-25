import { sparkline } from "@/lib/sparkline";
import type { SeriesPoint } from "@/lib/types";

/** Serial values as a small inline SVG (no chart library). */
export function Sparkline({ points, unit }: { points: SeriesPoint[]; unit: string | null }) {
  const geometry = sparkline(points);
  if (!geometry) return null;
  const summary = points.map((point) => `day ${point.day}: ${point.value}`).join(", ");
  return (
    <span className="inline-flex items-center gap-2">
      <svg width={120} height={28} viewBox="0 0 120 28" role="img" aria-label={summary} className="text-sky-700">
        <title>{summary}</title>
        <path d={geometry.path} fill="none" stroke="currentColor" strokeWidth={1.5} />
        {geometry.dots.map((dot) => (
          <circle key={dot.day} cx={dot.x} cy={dot.y} r={2} className={dot.flag ? "fill-red-600" : "fill-sky-700"} />
        ))}
      </svg>
      <span className="text-xs text-muted-foreground">
        {geometry.min}–{geometry.max}
        {unit ? ` ${unit}` : ""}
      </span>
    </span>
  );
}
