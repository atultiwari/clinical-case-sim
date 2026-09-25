import "server-only";

import { notFound } from "next/navigation";

import { parseCaseVersionId } from "@/lib/case-id";
import { getCaseOverview, type CaseOverview } from "@/server/queries/cases";

export type CaseParams = Promise<{ cv: string }>;

/** The case version named in the route, or the not-found page. */
export async function loadCase(params: CaseParams): Promise<CaseOverview> {
  const { cv } = await params;
  const id = parseCaseVersionId(cv);
  if (!id) notFound();
  const overview = await getCaseOverview(id);
  if (!overview) notFound();
  return overview;
}
