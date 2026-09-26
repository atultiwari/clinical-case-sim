import { getContext } from "@/lib/context";
import { getView } from "@/lib/game";
import { preflight, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** CORS preflight for the web build of the player app. */
export function OPTIONS(request: Request): Response {
  return preflight(request);
}

/** GET /api/encounters/:id/view: the PlayerView. */
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;
  return withPlayer(
    request,
    "reads",
    async ({ game }, playerId) => respond(await getView(game, playerId, id)),
    getContext,
  );
}
