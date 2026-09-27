import { getContext } from "@/lib/context";
import { commit } from "@/lib/game";
import { preflight, readJsonBody, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** CORS preflight for the web build of the player app. */
export function OPTIONS(request: Request): Response {
  return preflight(request);
}

/** POST /api/encounters/:id/commit { dx, evidence, plan, note? }: commits, scores and closes. */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;
  return withPlayer(
    request,
    "actions",
    async ({ game }, player) => {
      const body = await readJsonBody(request);
      return body.ok
        ? respond(await commit(game, player.playerId, id, body.body))
        : body.response;
    },
    getContext,
  );
}
