import type { ServerContext } from "./context";
import type { Outcome } from "./game";
import { bearerToken } from "./auth";
import type { RateLimiter } from "./rate-limit";

/**
 * The response envelope every endpoint uses: { success, data, error }. Errors never carry
 * stack traces or internal detail; those go to the server log.
 */

export interface Envelope<T> {
  readonly success: boolean;
  readonly data: T | null;
  readonly error: { readonly code: string; readonly message: string } | null;
}

export function respond<T>(outcome: Outcome<T>): Response {
  return outcome.ok
    ? Response.json({
        success: true,
        data: outcome.data,
        error: null,
      } satisfies Envelope<T>)
    : Response.json(
        {
          success: false,
          data: null,
          error: { code: outcome.error.code, message: outcome.error.message },
        } satisfies Envelope<T>,
        { status: outcome.error.status },
      );
}

const failure = (status: number, code: string, message: string): Response =>
  respond({ ok: false, error: { status, code, message } });

export async function readJsonBody(
  request: Request,
): Promise<{ ok: true; body: unknown } | { ok: false; response: Response }> {
  const text = await request.text();
  if (text.length > 20_000)
    return {
      ok: false,
      response: failure(413, "too_large", "The request is too large"),
    };
  try {
    return {
      ok: true,
      body: text.length === 0 ? {} : (JSON.parse(text) as unknown),
    };
  } catch {
    return {
      ok: false,
      response: failure(
        400,
        "invalid_json",
        "The request body is not valid JSON",
      ),
    };
  }
}

type Limit = keyof ServerContext["limits"];

/** Signs the request in, applies the rate limit, runs the handler and turns thrown errors into a 500. */
export async function withPlayer(
  request: Request,
  limit: Limit,
  handler: (context: ServerContext, playerId: string) => Promise<Response>,
  getContext: () => Promise<ServerContext>,
): Promise<Response> {
  try {
    const context = await getContext();
    const token = bearerToken(request.headers.get("authorization"));
    const player = token === null ? null : await context.verifier.verify(token);
    if (player === null) return failure(401, "unauthorised", "Sign in to play");
    const limiter: RateLimiter = context.limits[limit];
    if (!limiter.take(`${limit}:${player.playerId}`)) {
      return failure(
        429,
        "rate_limited",
        "Too many requests; wait a moment and try again",
      );
    }
    return await handler(context, player.playerId);
  } catch (error: unknown) {
    console.error("Game server error", error);
    return failure(500, "server_error", "Something went wrong on the server");
  }
}
