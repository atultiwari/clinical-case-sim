import type { Json } from "@/lib/ground-truth";

/**
 * component.ref_ranges: [{ "sex": "F", "age_min": 18, "age_max": 65, "low": 115, "high": 165 }].
 * Each range becomes one line, e.g. "F, 18–65 y: 115–165".
 */
export function formatRefRanges(value: Json | null | undefined, unit: string | null = null): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((entry) => {
    if (typeof entry !== "object" || entry === null || Array.isArray(entry)) return JSON.stringify(entry);
    const who = [
      typeof entry.sex === "string" && entry.sex !== "any" ? entry.sex : null,
      ageText(entry.age_min, entry.age_max),
    ].filter(Boolean);
    const range = rangeText(entry.low, entry.high);
    const withUnit = unit && range ? `${range} ${unit}` : range;
    return who.length > 0 ? `${who.join(", ")}: ${withUnit}` : withUnit;
  });
}

function isNumber(value: Json | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function ageText(min: Json | undefined, max: Json | undefined): string | null {
  if (isNumber(min) && isNumber(max)) return `${min}–${max} y`;
  if (isNumber(min)) return `≥ ${min} y`;
  if (isNumber(max)) return `≤ ${max} y`;
  return null;
}

function rangeText(low: Json | undefined, high: Json | undefined): string {
  if (isNumber(low) && isNumber(high)) return `${low}–${high}`;
  if (isNumber(low)) return `≥ ${low}`;
  if (isNumber(high)) return `≤ ${high}`;
  return "no range";
}
