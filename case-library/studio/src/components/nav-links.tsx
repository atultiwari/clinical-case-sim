"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/", label: "Cases", match: (path: string) => path === "/" || path.startsWith("/cases") },
  { href: "/catalogue", label: "Catalogue", match: (path: string) => path.startsWith("/catalogue") },
  { href: "/missing-requests", label: "Missing requests", match: (path: string) => path.startsWith("/missing-requests") },
];

export function NavLinks() {
  const pathname = usePathname();
  return (
    <nav className="flex gap-1">
      {LINKS.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={cn(
            "rounded-md px-2 py-1 no-underline hover:bg-muted",
            link.match(pathname) ? "bg-muted font-semibold" : "text-muted-foreground",
          )}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
