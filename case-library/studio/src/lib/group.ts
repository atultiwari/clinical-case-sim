export type Group<T> = { key: string; rows: T[] };

/** Rows grouped by a key, groups and rows in the order they first appear. */
export function groupBy<T>(rows: readonly T[], key: (row: T) => string): Group<T>[] {
  const groups = new Map<string, T[]>();
  for (const row of rows) {
    const k = key(row);
    groups.set(k, [...(groups.get(k) ?? []), row]);
  }
  return [...groups.entries()].map(([k, grouped]) => ({ key: k, rows: grouped }));
}
