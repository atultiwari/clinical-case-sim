import "server-only";

import { cache } from "react";

import type { Json } from "@/lib/ground-truth";
import { withReader } from "@/server/db";

export type CaseListRow = {
  id: string;
  case_id: string;
  version: number;
  status: string;
  source_type: string;
  specialty: string | null;
  display_title: string | null;
  pmcid: string | null;
  licence: string | null;
  production_ok: boolean | null;
  public_release_ok: boolean | null;
  curated_at: Date | null;
  coverage_total: number;
  coverage_resolved: number;
  fact_origins: Record<string, number>;
  ledger_tiers: Record<string, number>;
  open_review: number;
};

/** Every case version for the case list (SPEC §8), newest version first within a case. */
export async function listCaseVersions(): Promise<CaseListRow[]> {
  return withReader((sql) => sql<CaseListRow[]>`
    select cv.id, cv.case_id, cv.version, cv.status, c.source_type, c.specialty, c.display_title,
           s.pmcid, s.licence, s.production_ok, s.public_release_ok, cv.curated_at,
           cov.total as coverage_total, cov.resolved as coverage_resolved,
           (select coalesce(jsonb_object_agg(x.origin, x.n), '{}'::jsonb)
              from (select f.origin, count(*)::int as n from casevault.fact f
                    where f.case_version_id = cv.id group by f.origin) x) as fact_origins,
           (select coalesce(jsonb_object_agg(x.tier, x.n), '{}'::jsonb)
              from (select l.tier, count(*)::int as n from casevault.synthetic_ledger l
                    where l.case_version_id = cv.id and casevault.is_live(l.review_status)
                    group by l.tier) x) as ledger_tiers,
           ((select count(*) from casevault.fact f
              where f.case_version_id = cv.id and f.review_status = 'pending')
            + (select count(*) from casevault.synthetic_ledger l
              where l.case_version_id = cv.id and l.review_status = 'pending')
            + (select count(*) from casevault.report r
              where r.case_version_id = cv.id and r.review_status = 'pending')
            + (select count(*) from casevault.consult_note n
              where n.case_version_id = cv.id and n.review_status = 'pending'))::int as open_review
    from casevault.case_version cv
    join casevault."case" c on c.id = cv.case_id
    left join casevault.source_article s on s.id = c.source_id
    cross join lateral (
      select coalesce(sum(r.total), 0)::int as total, coalesce(sum(r.resolved), 0)::int as resolved
      from casevault.coverage_report(cv.id) r) cov
    order by cv.case_id, cv.version desc
  `);
}

export type CaseOverview = {
  id: string;
  case_id: string;
  version: number;
  schema_version: string;
  status: string;
  vignette: string | null;
  opening_statement_lay: string | null;
  day0_date: Date | null;
  day0_label: string | null;
  curated_by: string | null;
  skill_version: string | null;
  curated_at: Date | null;
  reviewed_by: string | null;
  frozen_at: Date | null;
  frozen_hash: string | null;
  source_type: string;
  slug: string | null;
  display_title: string | null;
  display_tags: string[];
  specialty: string | null;
  difficulty: string | null;
  est_minutes: number | null;
  lab_profile: Json | null;
  pmcid: string | null;
  doi: string | null;
  source_title: string | null;
  journal: string | null;
  published: Date | null;
  url: string | null;
  licence: string | null;
  licence_verified_at: Date | null;
  production_ok: boolean | null;
  public_release_ok: boolean | null;
  attribution: string | null;
};

/** One case version with its case and source (never the article's full text). */
export const getCaseOverview = cache(async (caseVersionId: string): Promise<CaseOverview | null> => {
  const rows = await withReader((sql) => sql<CaseOverview[]>`
    select cv.id, cv.case_id, cv.version, cv.schema_version, cv.status, cv.vignette,
           cv.opening_statement_lay, cv.day0_date, cv.day0_label, cv.curated_by, cv.skill_version,
           cv.curated_at, cv.reviewed_by, cv.frozen_at, cv.frozen_hash,
           c.source_type, c.slug, c.display_title, c.display_tags, c.specialty, c.difficulty,
           c.est_minutes, c.lab_profile,
           s.pmcid, s.doi, s.title as source_title, s.journal, s.published, s.url, s.licence,
           s.licence_verified_at, s.production_ok, s.public_release_ok, s.attribution
    from casevault.case_version cv
    join casevault."case" c on c.id = cv.case_id
    left join casevault.source_article s on s.id = c.source_id
    where cv.id = ${caseVersionId}
  `);
  return rows[0] ?? null;
});

export type BundleRow = {
  id: string;
  revision: number;
  catalogue_version: number;
  sha256: string | null;
  created_at: Date;
  published_at: Date | null;
  published_by: string | null;
};

export async function listBundles(caseVersionId: string): Promise<BundleRow[]> {
  return withReader((sql) => sql<BundleRow[]>`
    select id, revision, catalogue_version, sha256, created_at, published_at, published_by
    from casevault.bundle
    where case_version_id = ${caseVersionId}
    order by revision desc
  `);
}
