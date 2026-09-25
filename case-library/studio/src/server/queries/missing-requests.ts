import "server-only";

import { withReader } from "@/server/db";

export type MissingRequestGroup = {
  query: string;
  kind: string | null;
  frequency: number;
  statuses: string[];
  sources: string[];
  mapped_to: string[];
  first_seen: Date;
  last_seen: Date;
};

export const MISSING_REQUEST_LIMIT = 500;

/** Missing requests grouped by (normalised) query and kind, most frequent first. */
export async function listMissingRequests(): Promise<MissingRequestGroup[]> {
  return withReader((sql) => sql<MissingRequestGroup[]>`
    select min(query) as query, kind, count(*)::int as frequency,
           array_agg(distinct status order by status) as statuses,
           array_agg(distinct source order by source) as sources,
           coalesce(array_agg(distinct mapped_to order by mapped_to)
                    filter (where mapped_to is not null), '{}') as mapped_to,
           min(created_at) as first_seen, max(created_at) as last_seen
    from casevault.missing_request
    group by lower(btrim(query)), kind
    order by frequency desc, last_seen desc
    limit ${MISSING_REQUEST_LIMIT}
  `);
}
