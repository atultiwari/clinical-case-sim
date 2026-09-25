import { Empty, List, Section } from "@/components/common";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatCoverage, groupCoverageGaps, summariseCoverage } from "@/lib/coverage";
import { loadCase, type CaseParams } from "@/server/case-page";
import { COVERAGE_GAP_LIMIT, coverageReport, listCoverageGaps, listGapGuidance, listPaths } from "@/server/queries/paths";

const PATH_TONES = { efficient: "success", alternative: "info", trap: "danger" } as const;

export default async function PathsPage({ params }: { params: CaseParams }) {
  const c = await loadCase(params);
  const [paths, report, gaps, guidance] = await Promise.all([
    listPaths(c.id),
    coverageReport(c.id),
    listCoverageGaps(c.id),
    listGapGuidance(c.id),
  ]);
  const gapGroups = groupCoverageGaps(gaps);
  return (
    <>
      <Section title="Paths" aside={`${paths.length} paths`}>
        {paths.length === 0 ? (
          <Empty>No path analysis yet.</Empty>
        ) : (
          <Table>
            <TableBody>
              {paths.map((p) => (
                <TableRow key={p.path_id}>
                  <TableCell className="font-mono text-xs">{p.path_id}</TableCell>
                  <TableCell><Badge tone={PATH_TONES[p.kind as keyof typeof PATH_TONES] ?? "neutral"}>{p.kind}</Badge></TableCell>
                  <TableCell>
                    <div className="font-medium">{p.name}</div>
                    {p.rationale ? <div className="text-xs text-muted-foreground">{p.rationale}</div> : null}
                  </TableCell>
                  <TableCell><List items={p.items} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Section>
      <Section title="Coverage" aside={formatCoverage(summariseCoverage(report))}>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Kind</TableHead>
              <TableHead>Resolved</TableHead>
              <TableHead>Total</TableHead>
              <TableHead>Not yet resolved</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.map((row) => (
              <TableRow key={row.kind}>
                <TableCell>{row.kind}</TableCell>
                <TableCell>{row.resolved}</TableCell>
                <TableCell>{row.total}</TableCell>
                <TableCell>{row.missing.length}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Section>
      <Section
        title="Items not yet resolved"
        aside={gaps.length >= COVERAGE_GAP_LIMIT ? `first ${COVERAGE_GAP_LIMIT} gaps only` : `${gapGroups.length} items`}
      >
        {gapGroups.length === 0 ? (
          <Empty>Every active item resolves.</Empty>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Kind</TableHead>
                <TableHead>Item</TableHead>
                <TableHead>Components and days missing</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {gapGroups.map((g) => (
                <TableRow key={g.itemId}>
                  <TableCell>{g.kind}</TableCell>
                  <TableCell className="font-mono text-xs">{g.itemId}</TableCell>
                  <TableCell className="text-xs">
                    {g.components.length === 0
                      ? "no resolving row"
                      : g.components.map((cmp) => `${cmp.componentId} (days ${cmp.days.join(", ")})`).join("; ")}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Section>
      <Section title="Gaps and guidance" aside={`${guidance.length} gaps`}>
        {guidance.length === 0 ? (
          <Empty>No gap rows.</Empty>
        ) : (
          <Table>
            <TableBody>
              {guidance.map((g) => (
                <TableRow key={g.id}>
                  <TableCell className="font-mono text-xs">{g.id}</TableCell>
                  <TableCell>{g.item}</TableCell>
                  <TableCell className="text-xs">{g.guidance ?? "—"}</TableCell>
                  <TableCell>
                    {g.review_required ? <Badge tone="warning">review required</Badge> : null}
                    {g.auto_generate ? null : <Badge tone="muted">no auto-generate</Badge>}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Section>
    </>
  );
}
