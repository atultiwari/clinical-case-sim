/** Case version ids: 'PMC12949993@v1' or 'NID-0001@v2' (SPEC §1). */
const CASE_VERSION_ID = /^(PMC[0-9]+|NID-[0-9]{4,})@v[0-9]+$/;

/** The case version id from a route segment, or null if it is not one. */
export function parseCaseVersionId(segment: string): string | null {
  let decoded = segment;
  try {
    decoded = decodeURIComponent(segment);
  } catch {
    return null;
  }
  return CASE_VERSION_ID.test(decoded) ? decoded : null;
}

/** The route for a case version tab. */
export function caseHref(caseVersionId: string, tab = ""): string {
  const base = `/cases/${encodeURIComponent(caseVersionId)}`;
  return tab ? `${base}/${tab}` : base;
}
