import { getContext } from "@/lib/context";
import { getMe, saveMe } from "@/lib/game";
import { preflight, readJsonBody, respond, withPlayer } from "@/lib/http";

export const dynamic = "force-dynamic";

/** CORS preflight for the web build of the player app. */
export function OPTIONS(request: Request): Response {
  return preflight(request);
}

/** GET /api/me: the signed-in player's profile; 404 `no_profile` before the consent screen. */
export function GET(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "reads",
    async ({ game }, player) => respond(await getMe(game, player)),
    getContext,
  );
}

/** POST /api/me { nickname, trainingLevel, consentResearch, agreed: true }: creates or updates the profile. */
export function POST(request: Request): Promise<Response> {
  return withPlayer(
    request,
    "actions",
    async ({ game }, player) => {
      const body = await readJsonBody(request);
      return body.ok
        ? respond(await saveMe(game, player, body.body))
        : body.response;
    },
    getContext,
  );
}
