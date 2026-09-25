import { Badge } from "@/components/ui/badge";
import { licenceBadges, type LicenceFlags } from "@/lib/licence";
import { caseStatusLabel, caseStatusTone, humanise, reviewStatusTone, type Tone } from "@/lib/status";

export function CaseStatusBadge({ status }: { status: string }) {
  return <Badge tone={caseStatusTone(status)}>{caseStatusLabel(status)}</Badge>;
}

export function ReviewBadge({ status }: { status: string }) {
  return <Badge tone={reviewStatusTone(status)}>{humanise(status)}</Badge>;
}

export function LicenceBadges({ flags }: { flags: LicenceFlags }) {
  return (
    <span className="inline-flex flex-wrap gap-1">
      {licenceBadges(flags).map((badge) => (
        <Badge key={badge.label} tone={badge.tone} title={badge.title}>
          {badge.label}
        </Badge>
      ))}
    </span>
  );
}

const ORIGIN_TONES: Record<string, Tone> = {
  article: "success",
  derived: "info",
  affected: "warning",
  normal: "neutral",
  rule: "muted",
  reviewer: "info",
};

export function OriginBadge({ origin }: { origin: string }) {
  return <Badge tone={ORIGIN_TONES[origin] ?? "neutral"}>{origin}</Badge>;
}

export function FlagBadge({ on, label }: { on: boolean | null; label: string }) {
  return <Badge tone={on ? "success" : "muted"}>{`${label}: ${on ? "yes" : "no"}`}</Badge>;
}

/** Counts such as { article: 40, derived: 3 } as small origin badges. */
export function OriginCounts({ counts }: { counts: Record<string, number> }) {
  const entries = Object.entries(counts).filter(([, count]) => count > 0);
  if (entries.length === 0) return <span className="text-muted-foreground">—</span>;
  return (
    <span className="inline-flex flex-wrap gap-1">
      {entries.map(([origin, count]) => (
        <Badge key={origin} tone={ORIGIN_TONES[origin] ?? "neutral"}>
          {origin} {count}
        </Badge>
      ))}
    </span>
  );
}
