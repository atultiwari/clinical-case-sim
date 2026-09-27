import { getContext } from "@/lib/context";
import { listCases } from "@/lib/game";
import { preflight, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** CORS preflight for the web build of the player app. */
export function OPTIONS(request: Request): Response {
  return preflight(request);
}

/** GET /api/cases: the published case cards, newest revision each; no source identifiers. */
export function GET(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "reads",
    async ({ game }) => respond(await listCases(game)),
    getContext,
  );
}
