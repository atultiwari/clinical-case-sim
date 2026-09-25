import { FlagBadge, LicenceBadges } from "@/components/badges";
import { Empty, Fields } from "@/components/common";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime } from "@/lib/format";
import { loadCase, type CaseParams } from "@/server/case-page";
import { listMedia } from "@/server/queries/media";

const DECISION_TONES = { pending: "warning", use: "success", mask: "info", exclude: "danger" } as const;

export default async function FiguresPage({ params }: { params: CaseParams }) {
  const c = await loadCase(params);
  const media = await listMedia(c.id);
  if (media.length === 0) return <Empty>No figures.</Empty>;
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {media.map((m) => (
        <Card key={m.id}>
          <CardHeader>
            <CardTitle className="font-mono">{m.id}</CardTitle>
            <span className="text-muted-foreground">{[m.figure, m.specimen, m.stain].filter(Boolean).join(" · ")}</span>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-[160px_1fr]">
            <div
              className="flex h-32 items-center justify-center rounded-md border border-dashed bg-muted text-center text-xs text-muted-foreground"
              title="Figure images arrive in L0.8"
            >
              Image preview
              <br />
              comes in L0.8
            </div>
            <Fields
              rows={[
                ["File", m.file_path ? <code key="f" className="text-xs break-all">{m.file_path}</code> : null],
                ["Caption", m.redacted_caption],
                ["Licence", m.licence],
                [
                  "Flags",
                  <span key="flags" className="inline-flex flex-wrap gap-1">
                    <LicenceBadges flags={m} />
                    <FlagBadge on={m.production_ok} label="production_ok" />
                    <FlagBadge on={m.public_release_ok} label="public_release_ok" />
                  </span>,
                ],
                ["Annotations", m.has_annotations ? <Badge key="a" tone="warning">arrows or labels</Badge> : "none"],
                [
                  "Production decision",
                  <Badge key="d" tone={DECISION_TONES[m.production_decision as keyof typeof DECISION_TONES] ?? "neutral"}>
                    {m.production_decision}
                  </Badge>,
                ],
                ["Masked copy", m.masked_path],
                ["Decided", m.decided_by ? `${m.decided_by}, ${formatDateTime(m.decided_at)}` : null],
                ["Raw material", m.raw_fact_id],
              ]}
            />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
