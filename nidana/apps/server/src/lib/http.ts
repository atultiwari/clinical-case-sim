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

/**
 * CORS for the web build of the player app, which is served from another origin. Only origins
 * listed in NIDANA_ALLOWED_ORIGINS (comma-separated) are allowed; native apps do not need it.
 */
export function allowedOrigins(
  env: Record<string, string | undefined> = process.env,
): ReadonlySet<string> {
  return new Set(
    (env.NIDANA_ALLOWED_ORIGINS ?? "")
      .split(",")
      .map((o) => o.trim())
      .filter(Boolean),
  );
}

function corsHeaders(
  request: Request,
  allowed: ReadonlySet<string>,
): Record<string, string> {
  const origin = request.headers.get("origin");
  if (origin === null || !allowed.has(origin)) return { Vary: "Origin" };
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Headers": "authorization, content-type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Max-Age": "600",
    Vary: "Origin",
  };
}

/** Answers the browser's preflight request for every endpoint. */
export function preflight(
  request: Request,
  allowed: ReadonlySet<string> = allowedOrigins(),
): Response {
  return new Response(null, {
    status: 204,
    headers: corsHeaders(request, allowed),
  });
}

export function withCors(
  request: Request,
  response: Response,
  allowed: ReadonlySet<string> = allowedOrigins(),
): Response {
  for (const [key, value] of Object.entries(corsHeaders(request, allowed)))
    response.headers.set(key, value);
  return response;
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

/** Bytes a request body may hold. */
const MAX_BODY = 20_000;

/**
 * Reads the body as UTF-8 text, stopping as soon as it passes `limit` bytes, whatever the
 * headers claim, so an oversized or unbounded body is never buffered in full. Null if too large.
 */
export async function readBodyLimited(
  request: Request,
  limit: number = MAX_BODY,
): Promise<string | null> {
  if (Number(request.headers.get("content-length") ?? 0) > limit) return null;
  if (request.body === null) return "";
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > limit) {
      await reader.cancel();
      return null;
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(bytes);
}

export async function readJsonBody(
  request: Request,
): Promise<{ ok: true; body: unknown } | { ok: false; response: Response }> {
  const text = await readBodyLimited(request);
  if (text === null) {
    return {
      ok: false,
      response: failure(413, "too_large", "The request is too large"),
    };
  }
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
  return withCors(request, await signedIn(request, limit, handler, getContext));
}

async function signedIn(
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
