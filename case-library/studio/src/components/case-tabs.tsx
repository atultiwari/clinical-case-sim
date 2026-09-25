"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { caseHref } from "@/lib/case-id";
import { cn } from "@/lib/utils";

const TABS = [
  { segment: "", label: "Overview" },
  { segment: "facts", label: "Facts" },
  { segment: "ledger", label: "Ledger" },
  { segment: "reports", label: "Reports and consults" },
  { segment: "figures", label: "Figures" },
  { segment: "ground-truth", label: "Ground truth" },
  { segment: "paths", label: "Paths and coverage" },
  { segment: "review", label: "Review history" },
];

export function CaseTabs({ caseVersionId }: { caseVersionId: string }) {
  const pathname = usePathname();
  const base = caseHref(caseVersionId);
  const current = decodeURIComponent(pathname).replace(decodeURIComponent(base), "").replace(/^\//, "");
  return (
    <nav className="mb-4 flex flex-wrap gap-1 border-b">
      {TABS.map((tab) => (
        <Link
          key={tab.segment}
          href={caseHref(caseVersionId, tab.segment)}
          className={cn(
            "-mb-px border-b-2 px-2 py-1.5 no-underline",
            current === tab.segment
              ? "border-neutral-900 font-semibold"
              : "border-transparent text-muted-foreground hover:text-foreground",
          )}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}
