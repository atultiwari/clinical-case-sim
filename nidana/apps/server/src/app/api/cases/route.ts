import { getContext } from "@/lib/context";
import { listCases } from "@/lib/game";
import { respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** GET /api/cases: the published case cards, newest revision each; no source identifiers. */
export function GET(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "reads",
    async ({ game }) => respond(await listCases(game)),
    getContext,
  );
}
