import "server-only";

import type { CoverageGap, CoverageRow } from "@/lib/coverage";
import { withReader } from "@/server/db";

export type PathRow = { path_id: string; kind: string; name: string; rationale: string | null; items: string[] };
export type GapGuidanceRow = {
  id: string;
  item: string;
  guidance: string | null;
  review_required: boolean;
  auto_generate: boolean;
};

/** Enough to review by eye; the full list is in the review pack. */
export const COVERAGE_GAP_LIMIT = 2000;

export async function listPaths(caseVersionId: string): Promise<PathRow[]> {
  return withReader((sql) => sql<PathRow[]>`
    select path_id, kind, name, rationale, items
    from casevault.path_analysis
    where case_version_id = ${caseVersionId}
    order by array_position(array['efficient','alternative','trap'], kind), path_id
  `);
}

export async function coverageReport(caseVersionId: string): Promise<CoverageRow[]> {
  return withReader((sql) => sql<CoverageRow[]>`
    select kind, total, resolved, missing from casevault.coverage_report(${caseVersionId})
  `);
}

export async function listCoverageGaps(caseVersionId: string): Promise<CoverageGap[]> {
  return withReader((sql) => sql<CoverageGap[]>`
    select kind, item_id, component_id, day
    from casevault.coverage_gaps(${caseVersionId})
    limit ${COVERAGE_GAP_LIMIT}
  `);
}

export async function listGapGuidance(caseVersionId: string): Promise<GapGuidanceRow[]> {
  return withReader((sql) => sql<GapGuidanceRow[]>`
    select id, item, guidance, review_required, auto_generate
    from casevault.gap
    where case_version_id = ${caseVersionId}
    order by id
  `);
}
