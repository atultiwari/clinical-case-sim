const DATE_FORMAT = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" });
const DATE_TIME_FORMAT = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "UTC",
});
const INR = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });

function toDate(value: Date | string | null | undefined): Date | null {
  if (value === null || value === undefined) return null;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDate(value: Date | string | null | undefined): string {
  const date = toDate(value);
  return date ? DATE_FORMAT.format(date) : "—";
}

export function formatDateTime(value: Date | string | null | undefined): string {
  const date = toDate(value);
  return date ? `${DATE_TIME_FORMAT.format(date)} UTC` : "—";
}

export function formatPrice(value: number | null): string {
  return value === null ? "—" : INR.format(value);
}

/** Turnaround in minutes as '45 min', '2 h', '1 h 30 min' or '2 d'. */
export function formatTurnaround(minutes: number | null): string {
  if (minutes === null) return "—";
  if (minutes < 60) return `${minutes} min`;
  if (minutes % 1440 === 0) return `${minutes / 1440} d`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
}

/** 'Day 3', 'All admission' for null. */
export function formatDay(day: number | null): string {
  return day === null ? "All admission" : `Day ${day}`;
}
