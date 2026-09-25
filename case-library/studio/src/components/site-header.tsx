import Link from "next/link";

import { NavLinks } from "@/components/nav-links";
import { Badge } from "@/components/ui/badge";
import type { DatabaseHost } from "@/lib/db-host";

/** Top bar: the three screens, and which database the Studio is reading. */
export function SiteHeader({ host }: { host: DatabaseHost | null }) {
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-4 px-4 py-2">
        <Link href="/" className="font-semibold no-underline">
          Case Studio
        </Link>
        <NavLinks />
        <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
          <span>Read-only · Case Vault</span>
          {host ? (
            <Badge tone={host.local ? "neutral" : "warning"} title="Database host (no credentials)">
              {host.local ? "local" : "cloud"} · {host.host}:{host.port}/{host.database}
            </Badge>
          ) : (
            <Badge tone="danger">no database</Badge>
          )}
        </div>
      </div>
    </header>
  );
}
