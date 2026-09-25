import { Empty, List, PageTitle } from "@/components/common";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDateTime } from "@/lib/format";
import { MISSING_REQUEST_LIMIT, listMissingRequests } from "@/server/queries/missing-requests";

const STATUS_TONES = { new: "warning", mapped: "info", added: "success", ignored: "muted" } as const;

export default async function MissingRequestsPage() {
  const groups = await listMissingRequests();
  return (
    <>
      <PageTitle aside={groups.length >= MISSING_REQUEST_LIMIT ? `top ${MISSING_REQUEST_LIMIT} only` : `${groups.length} distinct requests`}>
        Missing requests
      </PageTitle>
      {groups.length === 0 ? (
        <Empty>No missing requests from Nidana or Sambhasha yet.</Empty>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Request</TableHead>
              <TableHead>Kind</TableHead>
              <TableHead className="text-right">Frequency</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Mapped to</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Last seen</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {groups.map((g) => (
              <TableRow key={`${g.kind ?? ""}|${g.query}`}>
                <TableCell>{g.query}</TableCell>
                <TableCell>{g.kind ?? "—"}</TableCell>
                <TableCell className="text-right font-semibold">{g.frequency}</TableCell>
                <TableCell>
                  <span className="inline-flex gap-1">
                    {g.statuses.map((s) => (
                      <Badge key={s} tone={STATUS_TONES[s as keyof typeof STATUS_TONES] ?? "neutral"}>{s}</Badge>
                    ))}
                  </span>
                </TableCell>
                <TableCell><List items={g.mapped_to} /></TableCell>
                <TableCell>{g.sources.join(", ")}</TableCell>
                <TableCell className="text-xs whitespace-nowrap">{formatDateTime(g.last_seen)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </>
  );
}
