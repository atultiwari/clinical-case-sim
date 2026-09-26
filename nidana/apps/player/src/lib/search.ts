import type { SearchItem } from "@nidana/contracts/api";

/** Catalogue search (N-006: every action is a catalogue item; free text is only a search box). */

export type SearchKind =
  "history" | "exam" | "test" | "referral" | "action" | "diagnosis";

const normalise = (text: string): string =>
  text
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();

function score(item: SearchItem, query: string): number {
  const name = normalise(item.name);
  if (name === query) return 100;
  if (name.startsWith(query)) return 80;
  const synonyms = item.synonyms.map(normalise);
  if (synonyms.some((s) => s === query)) return 75;
  if (name.split(" ").some((word) => word.startsWith(query))) return 60;
  if (synonyms.some((s) => s.startsWith(query))) return 50;
  const words = query.split(" ");
  const haystack = [name, ...synonyms].join(" ");
  return words.every((w) => haystack.includes(w)) ? 30 : 0;
}

/** Items of the given kinds that match the query, best first. An empty query matches nothing (search only, SPEC §5.9). */
export function searchItems(
  items: readonly SearchItem[],
  kinds: readonly SearchKind[],
  query: string,
  limit = 20,
): SearchItem[] {
  const q = normalise(query);
  if (q.length < 2) return [];
  return items
    .filter((item) => (kinds as readonly string[]).includes(item.kind))
    .map((item) => ({ item, score: score(item, q) }))
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score || a.item.name.localeCompare(b.item.name))
    .slice(0, limit)
    .map((r) => r.item);
}
