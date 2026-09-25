import { OriginBadge, ReviewBadge } from "@/components/badges";
import { Empty, List, Section } from "@/components/common";
import { JsonBlock } from "@/components/json-block";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { groupBy } from "@/lib/group";
import { loadCase, type CaseParams } from "@/server/case-page";
import { listConsultNotes, listReports, type ConsultNoteRow, type ReportRow } from "@/server/queries/reports";

export default async function ReportsPage({ params }: { params: CaseParams }) {
  const c = await loadCase(params);
  const [reports, notes] = await Promise.all([listReports(c.id), listConsultNotes(c.id)]);
  const reportGroups = groupBy(reports, (r) => r.test_item_id ?? "(no test)");
  const noteGroups = groupBy(notes, (n) => n.specialty);
  return (
    <>
      <Section title="Reports" aside={`${reports.length} variants`}>
        {reportGroups.length === 0 ? <Empty>No reports yet.</Empty> : null}
        {reportGroups.map((group) => (
          <div key={group.key} className="mb-4">
            <h3 className="mb-1 font-medium">
              <span className="font-mono">{group.key}</span>
              {group.rows[0]?.test_name ? <span className="text-muted-foreground"> · {group.rows[0].test_name}</span> : null}
            </h3>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {group.rows.map((report) => (
                <ReportCard key={report.id} report={report} />
              ))}
            </div>
          </div>
        ))}
      </Section>
      <Section title="Consult notes" aside={`${notes.length} variants`}>
        {noteGroups.length === 0 ? <Empty>No consult notes yet.</Empty> : null}
        {noteGroups.map((group) => (
          <div key={group.key} className="mb-4">
            <h3 className="mb-1 font-medium">
              <span className="font-mono">{group.key}</span>
              {group.rows[0]?.specialty_name ? <span className="text-muted-foreground"> · {group.rows[0].specialty_name}</span> : null}
            </h3>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {group.rows.map((note) => (
                <NoteCard key={note.id} note={note} />
              ))}
            </div>
          </div>
        ))}
      </Section>
    </>
  );
}

function ReportCard({ report }: { report: ReportRow }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-mono">{report.id}</CardTitle>
        <Badge tone="neutral">{report.variant}</Badge>
        <Badge tone={report.status === "final" ? "success" : "warning"}>{report.status}</Badge>
        <ReviewBadge status={report.review_status} />
      </CardHeader>
      <CardContent className="space-y-2">
        {report.status_line ? <p className="text-xs italic text-amber-900">{report.status_line}</p> : null}
        {report.report_text ? <p className="whitespace-pre-wrap">{report.report_text}</p> : null}
        {report.impression ? (
          <p>
            <span className="font-semibold">Impression: </span>
            {report.impression}
          </p>
        ) : null}
        <div className="text-xs">Findings: <List items={report.findings} /></div>
        <div className="text-xs">Suggested reflex: <List items={report.suggested_reflex} /></div>
        <div className="text-xs">Based on: <List items={report.based_on} /></div>
        <div className="flex flex-wrap gap-1">
          {report.origins.map((origin) => (
            <OriginBadge key={origin} origin={origin} />
          ))}
        </div>
        {report.review_note ? <p className="text-xs">Review note: {report.review_note}</p> : null}
      </CardContent>
    </Card>
  );
}

function NoteCard({ note }: { note: ConsultNoteRow }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-mono">{note.id}</CardTitle>
        <Badge tone="neutral">variant {note.variant}</Badge>
        <OriginBadge origin={note.origin} />
        <ReviewBadge status={note.review_status} />
      </CardHeader>
      <CardContent className="space-y-2">
        <div>
          <div className="text-xs text-muted-foreground">Condition</div>
          {note.condition === null ? <span className="text-xs">always (no condition)</span> : <JsonBlock value={note.condition} />}
        </div>
        <p className="whitespace-pre-wrap">{note.note_text}</p>
        {note.recommendations.length > 0 ? (
          <ul className="list-disc pl-5">
            {note.recommendations.map((recommendation) => (
              <li key={recommendation}>{recommendation}</li>
            ))}
          </ul>
        ) : null}
        {note.review_note ? <p className="text-xs">Review note: {note.review_note}</p> : null}
      </CardContent>
    </Card>
  );
}
