import "server-only";

import type { FactRow } from "@/lib/types";
import { withReader } from "@/server/db";

export async function listFacts(caseVersionId: string): Promise<FactRow[]> {
  return withReader((sql) => sql<FactRow[]>`
    select id, category, item, catalogue_ref, value, value_num::float8 as value_num, unit, ref_range,
           flag, day, kind, origin, formula, reveals_dx, pivotal, release, source_locator, review_status
    from casevault.fact
    where case_version_id = ${caseVersionId}
    order by category, day nulls first, id
  `);
}
