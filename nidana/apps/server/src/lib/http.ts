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

/** Bytes (as characters) a request body may hold. */
const MAX_BODY = 20_000;

export async function readJsonBody(
  request: Request,
): Promise<{ ok: true; body: unknown } | { ok: false; response: Response }> {
  // Refuse by the declared size first, so an oversized body is never read into memory.
  const declared = Number(request.headers.get("content-length") ?? 0);
  const text = declared > MAX_BODY ? "" : await request.text();
  if (declared > MAX_BODY || text.length > MAX_BODY)
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
    // Name and message only: a wrapped database error could carry parameter values.
    const detail =
      error instanceof Error
        ? `${error.name}: ${error.message}`
        : "unknown error";
    console.error("Game server error", detail);
    return failure(500, "server_error", "Something went wrong on the server");
  }
}
