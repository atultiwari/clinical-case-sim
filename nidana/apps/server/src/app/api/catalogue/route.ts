import { searchCatalogue } from "@/lib/catalogue";
import { getContext } from "@/lib/context";
import { preflight, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** CORS preflight for the web build of the player app. */
export function OPTIONS(request: Request): Response {
  return preflight(request);
}

/** GET /api/catalogue: names and synonyms for search, and test prices and turnaround. */
export function GET(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "reads",
    async ({ catalogue }) =>
      respond({ ok: true, data: searchCatalogue(catalogue) }),
    getContext,
  );
}
