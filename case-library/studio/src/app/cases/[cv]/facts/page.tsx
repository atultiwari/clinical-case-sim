import { OriginBadge, ReviewBadge } from "@/components/badges";
import { Empty, Section } from "@/components/common";
import { Sparkline } from "@/components/sparkline";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { groupFacts } from "@/lib/facts";
import { formatDay } from "@/lib/format";
import type { FactRow } from "@/lib/types";
import { loadCase, type CaseParams } from "@/server/case-page";
import { listFacts } from "@/server/queries/facts";

export default async function FactsPage({ params }: { params: CaseParams }) {
  const c = await loadCase(params);
  const groups = groupFacts(await listFacts(c.id));
  if (groups.length === 0) return <Empty>No facts yet.</Empty>;
  return (
    <>
      {groups.map((group) => (
        <Section key={group.category} title={group.category} aside={`${group.items.length} items`}>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-56">Item</TableHead>
                <TableHead className="w-48">Series</TableHead>
                <TableHead>Values</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {group.items.map((item) => (
                <TableRow key={item.key}>
                  <TableCell>
                    <div className="font-medium">{item.label}</div>
                    {item.key.startsWith("item:") ? null : (
                      <div className="font-mono text-xs text-muted-foreground">{item.key}</div>
                    )}
                  </TableCell>
                  <TableCell>{item.series ? <Sparkline points={item.series} unit={item.unit} /> : null}</TableCell>
                  <TableCell>
                    <ul className="space-y-1">
                      {item.rows.map((fact) => (
                        <FactLine key={fact.id} fact={fact} />
                      ))}
                    </ul>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Section>
      ))}
    </>
  );
}

function FactLine({ fact }: { fact: FactRow }) {
  const value = [fact.value ?? fact.value_num, fact.unit].filter((part) => part !== null && part !== "").join(" ");
  return (
    <li className="flex flex-wrap items-center gap-1.5">
      <span className="font-mono text-xs text-muted-foreground">{fact.id}</span>
      <span className="text-xs text-muted-foreground">{formatDay(fact.day)}</span>
      <span className={fact.flag ? "font-semibold text-red-700" : ""}>{value || "—"}</span>
      {fact.flag ? <Badge tone="danger">{fact.flag}</Badge> : null}
      {fact.ref_range ? <span className="text-xs text-muted-foreground">(ref {fact.ref_range})</span> : null}
      <OriginBadge origin={fact.origin} />
      {fact.kind === "interpretation" ? <Badge tone="muted">interpretation</Badge> : null}
      {fact.pivotal ? <Badge tone="info">pivotal</Badge> : null}
      {fact.reveals_dx ? <Badge tone="danger">reveals diagnosis</Badge> : null}
      <Badge tone="muted">{fact.release}</Badge>
      <ReviewBadge status={fact.review_status} />
      {fact.formula ? <span className="text-xs text-muted-foreground">= {fact.formula}</span> : null}
      {fact.source_locator ? <span className="text-xs text-muted-foreground">[{fact.source_locator}]</span> : null}
    </li>
  );
}
