import { firstParam, oneOf, pageNumber, toQueryString, type SearchParams } from "@/lib/search-params";

export const CATALOGUE_KINDS = ["history", "exam", "test", "action", "referral", "diagnosis", "finding"] as const;
export type CatalogueKind = (typeof CATALOGUE_KINDS)[number];
export const CATALOGUE_VIEWS = ["items", "components"] as const;
export type CatalogueView = (typeof CATALOGUE_VIEWS)[number];

export const CATALOGUE_PAGE_SIZE = 50;
const MAX_QUERY_LENGTH = 100;

export type CatalogueParams = {
  view: CatalogueView;
  kind?: CatalogueKind;
  q?: string;
  page: number;
};

export function parseCatalogueParams(params: SearchParams): CatalogueParams {
  const q = firstParam(params, "q");
  return {
    view: oneOf(firstParam(params, "view"), CATALOGUE_VIEWS) ?? "items",
    kind: oneOf(firstParam(params, "kind"), CATALOGUE_KINDS),
    q: q ? q.slice(0, MAX_QUERY_LENGTH) : undefined,
    page: pageNumber(firstParam(params, "page")),
  };
}

export function catalogueQuery(params: CatalogueParams, change: Partial<CatalogueParams>): string {
  const next = { ...params, page: 1, ...change };
  return toQueryString({
    view: next.view === "items" ? undefined : next.view,
    kind: next.view === "items" ? next.kind : undefined,
    q: next.q,
    page: next.page > 1 ? next.page : undefined,
  });
}

/** An ILIKE pattern that matches the text literally anywhere (escapes \, % and _). */
export function containsPattern(text: string): string {
  return `%${text.replace(/[\\%_]/g, (char) => `\\${char}`)}%`;
}

export function pageCount(total: number, pageSize: number): number {
  return Math.max(1, Math.ceil(total / pageSize));
}
