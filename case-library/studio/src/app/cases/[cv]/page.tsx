import { FlagBadge, LicenceBadges } from "@/components/badges";
import { Empty, Fields, List, Section } from "@/components/common";
import { JsonBlock } from "@/components/json-block";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate, formatDateTime } from "@/lib/format";
import { loadCase, type CaseParams } from "@/server/case-page";
import { listBundles } from "@/server/queries/cases";

export default async function OverviewPage({ params }: { params: CaseParams }) {
  const c = await loadCase(params);
  const bundles = await listBundles(c.id);
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <Section title="Source">
          {c.source_type === "de_novo" ? (
            <Empty>De novo case: no source article.</Empty>
          ) : (
            <Fields
              rows={[
                ["PMCID", c.pmcid],
                ["DOI", c.doi],
                ["Title", c.source_title],
                ["Journal", c.journal],
                ["Published", formatDate(c.published)],
                ["URL", c.url ? <a href={c.url} rel="noreferrer noopener" target="_blank">{c.url}</a> : null],
                ["Licence", c.licence],
                ["Licence verified", formatDateTime(c.licence_verified_at)],
                [
                  "Flags",
                  <span key="flags" className="inline-flex flex-wrap gap-1">
                    <LicenceBadges flags={c} />
                    <FlagBadge on={c.production_ok} label="production_ok" />
                    <FlagBadge on={c.public_release_ok} label="public_release_ok" />
                  </span>,
                ],
                ["Attribution", c.attribution],
              ]}
            />
          )}
        </Section>
        <Section title="Case">
          <Fields
            rows={[
              ["Neutral title", c.display_title],
              ["Slug", c.slug],
              ["Tags", <List key="tags" items={c.display_tags} />],
              ["Specialty", c.specialty],
              ["Difficulty", c.difficulty],
              ["Estimated minutes", c.est_minutes],
              ["Day 0", `${formatDate(c.day0_date)}${c.day0_label ? ` (${c.day0_label})` : ""}`],
              ["Schema version", c.schema_version],
            ]}
          />
        </Section>
        <Section title="Curation">
          <Fields
            rows={[
              ["Curated by", c.curated_by],
              ["Skill version", c.skill_version],
              ["Curated at", formatDateTime(c.curated_at)],
              ["Reviewed by", c.reviewed_by],
              ["Frozen at", formatDateTime(c.frozen_at)],
              ["Frozen hash", c.frozen_hash ? <code key="hash" className="text-xs">{c.frozen_hash}</code> : null],
            ]}
          />
        </Section>
      </div>
      <div>
        <Section title="Vignette">
          {c.vignette ? <p className="whitespace-pre-wrap">{c.vignette}</p> : <Empty>No vignette yet.</Empty>}
        </Section>
        <Section title="The patient's opening words">
          {c.opening_statement_lay ? (
            <blockquote className="border-l-4 pl-3 whitespace-pre-wrap italic">{c.opening_statement_lay}</blockquote>
          ) : (
            <Empty>No opening words yet.</Empty>
          )}
        </Section>
        <Section title="Laboratory profile">
          <JsonBlock value={c.lab_profile} />
        </Section>
        <Section title="Bundles">
          {bundles.length === 0 ? (
            <Empty>Not exported yet.</Empty>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Bundle</TableHead>
                  <TableHead>Catalogue</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Published</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bundles.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell className="font-mono">{b.id}</TableCell>
                    <TableCell>v{b.catalogue_version}</TableCell>
                    <TableCell>{formatDateTime(b.created_at)}</TableCell>
                    <TableCell>{b.published_at ? `${formatDateTime(b.published_at)} by ${b.published_by ?? "—"}` : "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Section>
      </div>
    </div>
  );
}
