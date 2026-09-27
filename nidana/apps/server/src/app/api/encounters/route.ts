import { getContext } from "@/lib/context";
import { listMyEncounters, startEncounter } from "@/lib/game";
import { preflight, readJsonBody, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** CORS preflight for the web build of the player app. */
export function OPTIONS(request: Request): Response {
  return preflight(request);
}

/** POST /api/encounters { slug, difficulty }: starts an encounter on the case's newest revision. */
export function POST(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "starts",
    async ({ game }, player) => {
      const body = await readJsonBody(request);
      return body.ok
        ? respond(await startEncounter(game, player, body.body))
        : body.response;
    },
    getContext,
  );
}

/** GET /api/encounters: the signed-in player's own encounters, newest first. */
export function GET(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "reads",
    async ({ game }, player) => respond(await listMyEncounters(game, player)),
    getContext,
  );
}
