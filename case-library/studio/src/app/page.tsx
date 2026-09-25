import Link from "next/link";

import { CaseStatusBadge, LicenceBadges, OriginCounts } from "@/components/badges";
import { Empty, PageTitle } from "@/components/common";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { caseHref } from "@/lib/case-id";
import { coverageOf, formatCoverage } from "@/lib/coverage";
import { listCaseVersions } from "@/server/queries/cases";

export default async function CaseListPage() {
  const cases = await listCaseVersions();
  return (
    <>
      <PageTitle aside={`${cases.length} case version${cases.length === 1 ? "" : "s"}`}>Cases</PageTitle>
      {cases.length === 0 ? (
        <Empty>No case versions in the Case Vault yet.</Empty>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Case version</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Specialty</TableHead>
              <TableHead>Licence</TableHead>
              <TableHead>Coverage</TableHead>
              <TableHead>Facts by origin</TableHead>
              <TableHead>Live ledger by tier</TableHead>
              <TableHead className="text-right">Open review items</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {cases.map((row) => (
              <TableRow key={row.id}>
                <TableCell>
                  <Link href={caseHref(row.id)} className="font-mono font-medium">
                    {row.id}
                  </Link>
                  {row.display_title ? <div className="text-xs text-muted-foreground">{row.display_title}</div> : null}
                </TableCell>
                <TableCell>
                  <CaseStatusBadge status={row.status} />
                </TableCell>
                <TableCell>{row.specialty ?? "—"}</TableCell>
                <TableCell>
                  {row.source_type === "de_novo" ? (
                    <Badge tone="neutral">De novo</Badge>
                  ) : (
                    <div className="flex flex-col gap-1">
                      <span className="text-xs">{row.licence ?? "—"}</span>
                      <LicenceBadges flags={row} />
                    </div>
                  )}
                </TableCell>
                <TableCell className="whitespace-nowrap">
                  {formatCoverage(coverageOf(row.coverage_resolved, row.coverage_total))}
                </TableCell>
                <TableCell>
                  <OriginCounts counts={row.fact_origins} />
                </TableCell>
                <TableCell>
                  <OriginCounts counts={row.ledger_tiers} />
                </TableCell>
                <TableCell className="text-right">
                  {row.open_review > 0 ? <Badge tone="warning">{row.open_review}</Badge> : "0"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </>
  );
}
