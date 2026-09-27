import type { ServerContext } from "./context";
import { respond } from "./http";

/**
 * The host's health check (N1.8): ok once the configuration, catalogue and settings load.
 * No sign-in and no detail, so it tells a stranger nothing about the server or its cases.
 */
export async function health(
  getContext: () => Promise<ServerContext>,
): Promise<Response> {
  try {
    await getContext();
    return respond({ ok: true, data: { status: "ok" } });
  } catch (error: unknown) {
    console.error(
      "Health check failed",
      error instanceof Error
        ? `${error.name}: ${error.message}`
        : "unknown error",
    );
    return respond({
      ok: false,
      error: {
        status: 503,
        code: "unavailable",
        message: "The game server is not ready",
      },
    });
  }
}
