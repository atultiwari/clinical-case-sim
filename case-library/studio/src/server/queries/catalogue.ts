import "server-only";

import { CATALOGUE_PAGE_SIZE, containsPattern, type CatalogueParams } from "@/lib/catalogue-params";
import type { Json } from "@/lib/ground-truth";
import { withReader } from "@/server/db";

export type TestComponentRef = { id: string; name: string; unit: string | null };

export type CatalogueItemRow = {
  id: string;
  kind: string;
  name: string;
  category: string | null;
  synonyms: string[];
  specialty_scope: string[];
  active: boolean;
  since_version: number;
  price_inr: number | null;
  price_source: string | null;
  tat_minutes: number | null;
  specimen: string | null;
  route: string | null;
  invasive: boolean | null;
  components: TestComponentRef[] | null;
};

export type ComponentRow = {
  id: string;
  name: string;
  loinc: string | null;
  unit_si: string | null;
  unit_conv: string | null;
  conv_factor: number | null;
  decimals: number | null;
  ref_ranges: Json | null;
  normal_text: string | null;
  tests: string[];
};

export type Page<T> = { rows: T[]; total: number; kindCounts: Record<string, number> };

function filters(params: CatalogueParams): { kind: string | null; pattern: string | null; offset: number } {
  return {
    kind: params.kind ?? null,
    pattern: params.q ? containsPattern(params.q) : null,
    offset: (params.page - 1) * CATALOGUE_PAGE_SIZE,
  };
}

/** Catalogue items matching a kind and a search over id, name and synonyms. */
export async function listCatalogueItems(params: CatalogueParams): Promise<Page<CatalogueItemRow>> {
  const { kind, pattern, offset } = filters(params);
  return withReader(async (sql) => {
    const condition = sql`
      (${kind}::text is null or i.kind = ${kind}::text)
        and (${pattern}::text is null or i.id ilike ${pattern}::text or i.name ilike ${pattern}::text
             or exists (select 1 from unnest(i.synonyms) s where s ilike ${pattern}::text))
    `;
    const rows = await sql<CatalogueItemRow[]>`
      select i.id, i.kind, i.name, i.category, i.synonyms, i.specialty_scope, i.active, i.since_version,
             t.price_inr::float8 as price_inr, t.price_source, t.tat_minutes, t.specimen, t.route,
             t.invasive,
             (select jsonb_agg(jsonb_build_object('id', c.id, 'name', c.name, 'unit', c.unit_si)
                               order by tc.position)
                from casevault.test_component tc
                join casevault.component c on c.id = tc.component_id
               where tc.test_item_id = i.id) as components
      from casevault.catalogue_item i
      left join casevault.test_def t on t.item_id = i.id
      where ${condition}
      order by i.kind, i.id
      limit ${CATALOGUE_PAGE_SIZE} offset ${offset}
    `;
    const [count] = await sql<{ total: number }[]>`
      select count(*)::int as total from casevault.catalogue_item i where ${condition}
    `;
    const [kinds] = await sql<{ counts: Record<string, number> }[]>`
      select coalesce(jsonb_object_agg(x.kind, x.n), '{}'::jsonb) as counts
      from (select kind, count(*)::int as n from casevault.catalogue_item group by kind) x
    `;
    return { rows, total: count?.total ?? 0, kindCounts: kinds?.counts ?? {} };
  });
}

/** Components with units and reference ranges, searched by id and name. */
export async function listComponents(params: CatalogueParams): Promise<Page<ComponentRow>> {
  const { pattern, offset } = filters(params);
  return withReader(async (sql) => {
    const matching = sql`
      from casevault.component c
      where (${pattern}::text is null or c.id ilike ${pattern}::text or c.name ilike ${pattern}::text)
    `;
    const rows = await sql<ComponentRow[]>`
      select c.id, c.name, c.loinc, c.unit_si, c.unit_conv, c.conv_factor::float8 as conv_factor,
             c.decimals, c.ref_ranges, c.normal_text,
             coalesce((select array_agg(tc.test_item_id order by tc.test_item_id)
                         from casevault.test_component tc where tc.component_id = c.id), '{}') as tests
      ${matching}
      order by c.id
      limit ${CATALOGUE_PAGE_SIZE} offset ${offset}
    `;
    const [count] = await sql<{ total: number }[]>`select count(*)::int as total ${matching}`;
    return { rows, total: count?.total ?? 0, kindCounts: {} };
  });
}
