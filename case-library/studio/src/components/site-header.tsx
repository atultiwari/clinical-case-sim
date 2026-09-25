import Link from "next/link";

import { NavLinks } from "@/components/nav-links";
import { Badge } from "@/components/ui/badge";
import type { DatabaseHost } from "@/lib/db-host";
import { logout } from "@/server/actions/session";

type Props = {
  host: DatabaseHost | null;
  /** The logged-in username, when the Studio has a login. */
  user: string | null;
  /** Whether the Studio can record decisions (login configured and the writer URL set). */
  writable: boolean;
};

/** Top bar: the three screens, which database the Studio is reading, and who is logged in. */
export function SiteHeader({ host, user, writable }: Props) {
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-4 px-4 py-2">
        <Link href="/" className="font-semibold no-underline">
          Case Studio
        </Link>
        <NavLinks />
        <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
          <span>{writable ? "Review" : "Read-only"} · Case Vault</span>
          {host ? (
            <Badge tone={host.local ? "neutral" : "warning"} title="Database host (no credentials)">
              {host.local ? "local" : "cloud"} · {host.host}:{host.port}/{host.database}
            </Badge>
          ) : (
            <Badge tone="danger">no database</Badge>
          )}
          {user ? (
            <form action={logout} className="flex items-center gap-2">
              <span className="font-medium text-foreground">{user}</span>
              <button type="submit" className="rounded-md border px-2 py-0.5 hover:bg-muted">
                Log out
              </button>
            </form>
          ) : null}
        </div>
      </div>
    </header>
  );
}
