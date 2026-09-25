import Link from "next/link";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function PageTitle({ children, aside }: { children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="mb-3 flex flex-wrap items-baseline gap-3">
      <h1 className="text-lg font-semibold">{children}</h1>
      {aside ? <div className="text-xs text-muted-foreground">{aside}</div> : null}
    </div>
  );
}

export function Section({ title, children, aside }: { title: string; children: ReactNode; aside?: ReactNode }) {
  return (
    <section className="mb-6">
      <div className="mb-2 flex flex-wrap items-baseline gap-2">
        <h2 className="text-base font-semibold">{title}</h2>
        {aside ? <span className="text-xs text-muted-foreground">{aside}</span> : null}
      </div>
      {children}
    </section>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="rounded-md border border-dashed p-4 text-muted-foreground">{children}</p>;
}

export function Fields({ rows }: { rows: [string, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1">
      {rows.map(([label, value]) => (
        <div key={label} className="contents">
          <dt className="text-muted-foreground">{label}</dt>
          <dd>{value === null || value === undefined || value === "" ? "—" : value}</dd>
        </div>
      ))}
    </dl>
  );
}

export type FilterOption = { label: string; href: string; active: boolean; count?: number };

/** A row of link chips: filters kept in the URL, so every view can be bookmarked. */
export function FilterLinks({ label, options }: { label: string; options: FilterOption[] }) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      <span className="w-28 text-xs text-muted-foreground">{label}</span>
      {options.map((option) => (
        <Link
          key={option.label}
          href={option.href}
          className={cn(
            "rounded-md border px-2 py-0.5 text-xs no-underline",
            option.active ? "border-neutral-800 bg-neutral-800 text-white" : "hover:bg-muted",
          )}
        >
          {option.label}
          {option.count !== undefined ? ` (${option.count})` : ""}
        </Link>
      ))}
    </div>
  );
}

export function Pager({ page, pages, href }: { page: number; pages: number; href: (page: number) => string }) {
  if (pages <= 1) return null;
  return (
    <div className="mt-2 flex items-center gap-3 text-xs">
      {page > 1 ? <Link href={href(page - 1)}>← Previous</Link> : <span className="text-muted-foreground">← Previous</span>}
      <span>
        Page {page} of {pages}
      </span>
      {page < pages ? <Link href={href(page + 1)}>Next →</Link> : <span className="text-muted-foreground">Next →</span>}
    </div>
  );
}

export function List({ items }: { items: readonly string[] }) {
  if (items.length === 0) return <span className="text-muted-foreground">—</span>;
  return <span className="font-mono text-xs">{items.join(", ")}</span>;
}
