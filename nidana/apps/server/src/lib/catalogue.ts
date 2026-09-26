import type { CatalogueExport } from "@nidana/contracts";
import { SEAT } from "@nidana/engine";

/**
 * What the app searches (SPEC §6.2 `GET /api/catalogue`): every item the Attending can use, with
 * names and synonyms, and prices and turnaround for tests. It lists every diagnosis for every
 * case, so it reveals nothing about one case, and the leak tests leave it out of the word scan.
 */

export interface SearchItem {
  readonly id: string;
  readonly kind: string;
  readonly name: string;
  readonly category: string;
  readonly synonyms: readonly string[];
  readonly priceInr?: number | null;
  readonly turnaroundMinutes?: number | null;
}

const PLAYER_KINDS = new Set([
  "history",
  "exam",
  "test",
  "referral",
  "action",
  "diagnosis",
]);

export function searchCatalogue(catalogue: CatalogueExport): SearchItem[] {
  const tests = new Map(catalogue.tests.map((t) => [t.item_id, t]));
  return catalogue.items
    .filter(
      (item) =>
        PLAYER_KINDS.has(item.kind) &&
        (item.kind === "diagnosis" || item.specialty_scope.includes(SEAT)),
    )
    .map((item) => {
      const test = tests.get(item.id);
      const base = {
        id: item.id,
        kind: item.kind,
        name: item.name,
        category: item.category,
        synonyms: item.synonyms,
      };
      return test === undefined
        ? base
        : {
            ...base,
            priceInr: test.price_inr,
            turnaroundMinutes: test.tat_minutes,
          };
    });
}
