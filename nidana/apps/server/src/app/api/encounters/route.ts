import { getContext } from "@/lib/context";
import { startEncounter } from "@/lib/game";
import { readJsonBody, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** POST /api/encounters { slug, difficulty }: starts an encounter on the case's newest revision. */
export function POST(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "starts",
    async ({ game }, playerId) => {
      const body = await readJsonBody(request);
      return body.ok
        ? respond(await startEncounter(game, playerId, body.body))
        : body.response;
    },
    getContext,
  );
}
