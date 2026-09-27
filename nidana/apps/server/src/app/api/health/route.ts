import { getContext } from "@/lib/context";
import { health } from "@/lib/health";

export const dynamic = "force-dynamic";

/** GET /api/health: for the host's health check (no sign-in, no detail). */
export function GET(): Promise<Response> {
  return health(getContext);
}
