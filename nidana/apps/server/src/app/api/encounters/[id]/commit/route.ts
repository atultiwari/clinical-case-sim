import { getContext } from "@/lib/context";
import { commit } from "@/lib/game";
import { readJsonBody, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** POST /api/encounters/:id/commit { dx, evidence, plan, note? }: commits, scores and closes. */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;
  return withPlayer(
    request,
    "actions",
    async ({ game }, playerId) => {
      const body = await readJsonBody(request);
      return body.ok
        ? respond(await commit(game, playerId, id, body.body))
        : body.response;
    },
    getContext,
  );
}
