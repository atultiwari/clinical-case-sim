/** Where the Studio reads from, without credentials, for the page banner. */
export type DatabaseHost = {
  host: string;
  port: string;
  database: string;
  local: boolean;
};

const LOCAL_HOSTS = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);

export function describeDatabaseHost(url: string): DatabaseHost | null {
  try {
    const parsed = new URL(url);
    if (!parsed.protocol.startsWith("postgres")) return null;
    const host = parsed.hostname;
    return {
      host,
      port: parsed.port || "5432",
      database: decodeURIComponent(parsed.pathname.replace(/^\//, "")) || "postgres",
      local: LOCAL_HOSTS.has(host),
    };
  } catch {
    return null;
  }
}
