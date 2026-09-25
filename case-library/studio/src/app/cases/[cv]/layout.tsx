import type { ReactNode } from "react";

import { CaseStatusBadge, LicenceBadges } from "@/components/badges";
import { CaseTabs } from "@/components/case-tabs";
import { Badge } from "@/components/ui/badge";
import { loadCase, type CaseParams } from "@/server/case-page";

export default async function CaseLayout({ children, params }: { children: ReactNode; params: CaseParams }) {
  const overview = await loadCase(params);
  return (
    <>
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h1 className="font-mono text-lg font-semibold">{overview.id}</h1>
        <CaseStatusBadge status={overview.status} />
        {overview.source_type === "de_novo" ? <Badge>De novo</Badge> : <LicenceBadges flags={overview} />}
        <span className="text-muted-foreground">
          {[overview.display_title, overview.specialty].filter(Boolean).join(" · ")}
        </span>
      </div>
      <p className="mb-2 text-xs text-red-700">Contains the diagnosis and answers. Private: never share outside the Studio.</p>
      <CaseTabs caseVersionId={overview.id} />
      {children}
    </>
  );
}
