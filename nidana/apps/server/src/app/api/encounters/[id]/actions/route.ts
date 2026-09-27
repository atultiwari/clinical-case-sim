import { getContext } from "@/lib/context";
import { act } from "@/lib/game";
import { preflight, readJsonBody, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** CORS preflight for the web build of the player app. */
export function OPTIONS(request: Request): Response {
  return preflight(request);
}

/** POST /api/encounters/:id/actions: validates and appends one action; returns the PlayerView. */
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
        ? respond(await act(game, player.playerId, id, body.body))
        : body.response;
    },
    getContext,
  );
}
