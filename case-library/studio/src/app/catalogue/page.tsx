import { Empty, FilterLinks, PageTitle, Pager } from "@/components/common";
import { ComponentTable, ItemTable } from "@/components/catalogue-tables";
import {
  CATALOGUE_KINDS,
  CATALOGUE_PAGE_SIZE,
  catalogueQuery,
  pageCount,
  parseCatalogueParams,
} from "@/lib/catalogue-params";
import type { SearchParams } from "@/lib/search-params";
import { listCatalogueItems, listComponents } from "@/server/queries/catalogue";

export default async function CataloguePage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const params = parseCatalogueParams(await searchParams);
  const isItems = params.view === "items";
  const result = isItems
    ? { view: "items" as const, page: await listCatalogueItems(params) }
    : { view: "components" as const, page: await listComponents(params) };
  const { page } = result;
  const base = "/catalogue";
  const kindTotal = Object.values(page.kindCounts).reduce((sum, n) => sum + n, 0);
  return (
    <>
      <PageTitle aside={`${page.total} matching`}>Catalogue</PageTitle>
      <div className="mb-3 space-y-1">
        <FilterLinks
          label="View"
          options={[
            { label: "Items", href: base + catalogueQuery(params, { view: "items" }), active: isItems },
            { label: "Components", href: base + catalogueQuery(params, { view: "components" }), active: !isItems },
          ]}
        />
        {isItems ? (
          <FilterLinks
            label="Kind"
            options={[
              { label: "all", href: base + catalogueQuery(params, { kind: undefined }), active: !params.kind, count: kindTotal },
              ...CATALOGUE_KINDS.map((kind) => ({
                label: kind,
                href: base + catalogueQuery(params, { kind }),
                active: params.kind === kind,
                count: page.kindCounts[kind] ?? 0,
              })),
            ]}
          />
        ) : null}
        <form action={base} className="flex items-center gap-1">
          <span className="w-28 text-xs text-muted-foreground">Search</span>
          {isItems ? null : <input type="hidden" name="view" value="components" />}
          {params.kind && isItems ? <input type="hidden" name="kind" value={params.kind} /> : null}
          <input
            name="q"
            defaultValue={params.q}
            placeholder={isItems ? "id, name or synonym" : "id or name"}
            className="w-64 rounded-md border px-2 py-0.5 text-xs"
          />
          <button type="submit" className="rounded-md border px-2 py-0.5 text-xs hover:bg-muted">Search</button>
        </form>
      </div>
      {page.rows.length === 0 ? (
        <Empty>Nothing matches.</Empty>
      ) : result.view === "items" ? (
        <ItemTable rows={result.page.rows} />
      ) : (
        <ComponentTable rows={result.page.rows} />
      )}
      <Pager
        page={params.page}
        pages={pageCount(page.total, CATALOGUE_PAGE_SIZE)}
        href={(n) => base + catalogueQuery(params, { page: n })}
      />
    </>
  );
}
