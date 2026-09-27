import type {
  ActionRequest,
  CaseCard,
  CommitRequest,
  CommitResult,
  DebriefView,
  Envelope,
  MissingRequest,
  PlayerView,
  SearchItem,
  StartRequest,
} from "@nidana/contracts/api";

/** The game server's API (SPEC §6.2). Every request carries the player's access token. */

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export interface Api {
  cases(): Promise<CaseCard[]>;
  catalogue(): Promise<SearchItem[]>;
  start(request: StartRequest): Promise<PlayerView>;
  view(encounterId: string): Promise<PlayerView>;
  act(encounterId: string, action: ActionRequest): Promise<PlayerView>;
  commit(encounterId: string, request: CommitRequest): Promise<CommitResult>;
  debrief(encounterId: string): Promise<DebriefView>;
  missing(request: MissingRequest): Promise<void>;
}

type Fetch = (input: string, init: RequestInit) => Promise<Response>;

// Browsers refuse a detached `fetch` ("Illegal invocation"), so the default calls it through globalThis.
const globalFetch: Fetch = (input, init) => globalThis.fetch(input, init);

export function createApi(
  baseUrl: string,
  getToken: () => Promise<string>,
  fetcher: Fetch = globalFetch,
): Api {
  async function call<T>(
    method: "GET" | "POST",
    path: string,
    body?: unknown,
  ): Promise<T> {
    let token: string;
    try {
      token = await getToken();
    } catch (error: unknown) {
      const detail = error instanceof Error ? error.message : "unknown reason";
      throw new ApiError(
        401,
        "sign_in_failed",
        `Could not sign you in (${detail}). Try again in a moment.`,
      );
    }
    let response: Response;
    try {
      response = await fetcher(`${baseUrl}${path}`, {
        method,
        headers: {
          authorization: `Bearer ${token}`,
          ...(body === undefined ? {} : { "content-type": "application/json" }),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch {
      throw new ApiError(
        0,
        "offline",
        "The game server could not be reached. Check your connection and try again.",
      );
    }
    let envelope: Envelope<T>;
    try {
      envelope = (await response.json()) as Envelope<T>;
    } catch {
      throw new ApiError(
        response.status,
        "bad_response",
        "The game server sent an unexpected reply.",
      );
    }
    if (!envelope.success || envelope.data === null) {
      throw new ApiError(
        response.status,
        envelope.error?.code ?? "error",
        envelope.error?.message ?? "Something went wrong.",
      );
    }
    return envelope.data;
  }

  const id = (encounterId: string): string => encodeURIComponent(encounterId);
  return {
    cases: () => call("GET", "/api/cases"),
    catalogue: () => call("GET", "/api/catalogue"),
    start: (request) => call("POST", "/api/encounters", request),
    view: (encounterId) =>
      call("GET", `/api/encounters/${id(encounterId)}/view`),
    act: (encounterId, action) =>
      call("POST", `/api/encounters/${id(encounterId)}/actions`, action),
    commit: (encounterId, request) =>
      call("POST", `/api/encounters/${id(encounterId)}/commit`, request),
    debrief: (encounterId) =>
      call("GET", `/api/encounters/${id(encounterId)}/debrief`),
    missing: async (request) => {
      await call("POST", "/api/missing", request);
    },
  };
}
