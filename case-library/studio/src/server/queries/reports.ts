import "server-only";

import type { Json } from "@/lib/ground-truth";
import { withReader } from "@/server/db";

export type ReportRow = {
  id: string;
  test_item_id: string | null;
  test_name: string | null;
  variant: string;
  status: string;
  status_line: string | null;
  findings: string[];
  report_text: string | null;
  impression: string | null;
  suggested_reflex: string[];
  based_on: string[];
  origins: string[];
  generator: string;
  review_status: string;
  review_note: string | null;
};

export type ConsultNoteRow = {
  id: string;
  specialty: string;
  specialty_name: string | null;
  variant: number;
  condition: Json | null;
  note_text: string;
  recommendations: string[];
  origin: string;
  generator: string;
  review_status: string;
  review_note: string | null;
};

export async function listReports(caseVersionId: string): Promise<ReportRow[]> {
  return withReader((sql) => sql<ReportRow[]>`
    select r.id, r.test_item_id, ci.name as test_name, r.variant, r.status, r.status_line, r.findings,
           r.report_text, r.impression, r.suggested_reflex, r.based_on, r.origins, r.generator,
           r.review_status, r.review_note
    from casevault.report r
    left join casevault.catalogue_item ci on ci.id = r.test_item_id
    where r.case_version_id = ${caseVersionId}
    order by r.test_item_id nulls last,
             array_position(array['original', 'expert', 'only'], r.variant), r.id
  `);
}

export async function listConsultNotes(caseVersionId: string): Promise<ConsultNoteRow[]> {
  return withReader((sql) => sql<ConsultNoteRow[]>`
    select n.id, n.specialty, ci.name as specialty_name, n.variant, n.condition, n.note_text,
           n.recommendations, n.origin, n.generator, n.review_status, n.review_note
    from casevault.consult_note n
    left join casevault.catalogue_item ci on ci.id = n.specialty
    where n.case_version_id = ${caseVersionId}
    order by n.specialty, n.variant, n.id
  `);
}
