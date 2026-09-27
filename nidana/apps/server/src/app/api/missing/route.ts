import { getContext } from "@/lib/context";
import { logMissing } from "@/lib/game";
import { preflight, readJsonBody, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** CORS preflight for the web build of the player app. */
export function OPTIONS(request: Request): Response {
  return preflight(request);
}

/** POST /api/missing { encounterId, kind, query }: logs a search with no match. */
export function POST(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "actions",
    async ({ game }, playerId) => {
      const body = await readJsonBody(request);
      return body.ok
        ? respond(await logMissing(game, playerId, body.body))
        : body.response;
    },
    getContext,
  );
}
