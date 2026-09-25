import "server-only";

import { withReader } from "@/server/db";

export type MediaRow = {
  id: string;
  figure: string | null;
  specimen: string | null;
  stain: string | null;
  file_path: string | null;
  redacted_caption: string | null;
  licence: string;
  production_ok: boolean;
  public_release_ok: boolean;
  has_annotations: boolean;
  production_decision: string;
  masked_path: string | null;
  decided_by: string | null;
  decided_at: Date | null;
  raw_fact_id: string | null;
};

export async function listMedia(caseVersionId: string): Promise<MediaRow[]> {
  return withReader((sql) => sql<MediaRow[]>`
    select id, figure, specimen, stain, file_path, redacted_caption, licence, production_ok,
           public_release_ok, has_annotations, production_decision, masked_path, decided_by,
           decided_at, raw_fact_id
    from casevault.media
    where case_version_id = ${caseVersionId}
    order by id
  `);
}
