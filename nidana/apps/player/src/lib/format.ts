/** Display helpers. British English (N-019); simulated time is minutes from arrival on day 0. */

const pad = (n: number): string => String(n).padStart(2, "0");

/** "Day 0, 04:45" */
export function formatClock(minutes: number): string {
  const day = Math.floor(minutes / 1440);
  const within = minutes - day * 1440;
  return `Day ${day}, ${pad(Math.floor(within / 60))}:${pad(within % 60)}`;
}

/** "4 h", "30 min", "1 day 2 h" */
export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const rest = minutes % 60;
  const parts = [
    days > 0 ? `${days} day${days === 1 ? "" : "s"}` : "",
    hours > 0 ? `${hours} h` : "",
    rest > 0 && days === 0 ? `${rest} min` : "",
  ];
  return parts.filter(Boolean).join(" ");
}

/** "₹1,500" (Indian digit grouping). */
export function formatInr(amount: number): string {
  return `₹${Math.round(amount).toLocaleString("en-IN")}`;
}
