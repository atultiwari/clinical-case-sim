import { getContext } from "@/lib/context";
import { credits } from "@/lib/game";
import { preflight, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** CORS preflight for the web build of the player app. */
export function OPTIONS(request: Request): Response {
  return preflight(request);
}

/** GET /api/credits: the attribution of every case the player can see (SPEC §12). */
export function GET(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "reads",
    async ({ game }, player) => respond(await credits(game, player)),
    getContext,
  );
}
