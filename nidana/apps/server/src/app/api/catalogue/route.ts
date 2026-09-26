import { searchCatalogue } from "@/lib/catalogue";
import { getContext } from "@/lib/context";
import { respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

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
