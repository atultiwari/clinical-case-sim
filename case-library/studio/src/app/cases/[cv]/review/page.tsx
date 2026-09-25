import { OriginBadge } from "@/components/badges";
import { Empty, Section } from "@/components/common";
import { JsonBlock } from "@/components/json-block";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDateTime, formatDay } from "@/lib/format";
import { prettyJson } from "@/lib/ground-truth";
import { loadCase, type CaseParams } from "@/server/case-page";
import { DECISION_LIMIT, listReviewBatches, listReviewDecisions, listSupersededLedger } from "@/server/queries/review";

const DECISION_TONES = { approve: "success", edit: "info", reject: "danger" } as const;

export default async function ReviewPage({ params }: { params: CaseParams }) {
  const c = await loadCase(params);
  const [batches, decisions, superseded] = await Promise.all([
    listReviewBatches(c.id),
    listReviewDecisions(c.id),
    listSupersededLedger(c.id),
  ]);
  return (
    <>
      <Section title="Review batches" aside={`${batches.length} batches`}>
        {batches.length === 0 ? (
          <Empty>Not in a review batch yet.</Empty>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Batch</TableHead>
                <TableHead>Case versions</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Returned</TableHead>
                <TableHead>Applied</TableHead>
                <TableHead>Decisions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {batches.map((b) => (
                <TableRow key={b.id}>
                  <TableCell className="font-mono text-xs">{b.id}</TableCell>
                  <TableCell className="font-mono text-xs">{b.case_version_ids.join(", ")}</TableCell>
                  <TableCell>{formatDateTime(b.created_at)}</TableCell>
                  <TableCell>{formatDateTime(b.returned_at)}</TableCell>
                  <TableCell>{formatDateTime(b.applied_at)}</TableCell>
                  <TableCell>{b.decisions}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Section>
      <Section
        title="Decisions"
        aside={decisions.length >= DECISION_LIMIT ? `latest ${DECISION_LIMIT} only` : `${decisions.length} decisions`}
      >
        {decisions.length === 0 ? (
          <Empty>No decisions recorded.</Empty>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Decided</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Decision</TableHead>
                <TableHead>Edited</TableHead>
                <TableHead>Note</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {decisions.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="text-xs whitespace-nowrap">
                    {formatDateTime(d.decided_at)}
                    <div className="text-muted-foreground">{d.decided_by} · {d.batch_id}</div>
                  </TableCell>
                  <TableCell className="font-mono text-xs">{d.target_table}:{d.target_id}</TableCell>
                  <TableCell><Badge tone={DECISION_TONES[d.decision as keyof typeof DECISION_TONES] ?? "neutral"}>{d.decision}</Badge></TableCell>
                  <TableCell className="w-1/3">{d.edited === null ? "—" : <JsonBlock value={d.edited} />}</TableCell>
                  <TableCell className="text-xs">{d.note ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Section>
      <Section title="Superseded ledger rows" aside={`${superseded.length} rows`}>
        {superseded.length === 0 ? (
          <Empty>No superseded rows.</Empty>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Target</TableHead>
                <TableHead>Day</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead>Old value</TableHead>
                <TableHead>Replaced by</TableHead>
                <TableHead>Note</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {superseded.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="font-mono text-xs">{row.target}</TableCell>
                  <TableCell>{formatDay(row.day_bucket)}</TableCell>
                  <TableCell><OriginBadge origin={row.tier} /></TableCell>
                  <TableCell><code className="text-xs break-all">{prettyJson(row.value)}</code></TableCell>
                  <TableCell className="font-mono text-xs">{row.replaced_by ?? "—"}</TableCell>
                  <TableCell className="text-xs">{row.review_note ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Section>
    </>
  );
}
