import { List } from "@/components/common";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatPrice, formatTurnaround } from "@/lib/format";
import { formatRefRanges } from "@/lib/ref-ranges";
import type { CatalogueItemRow, ComponentRow } from "@/server/queries/catalogue";

export function ItemTable({ rows }: { rows: CatalogueItemRow[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Id</TableHead>
          <TableHead>Name and synonyms</TableHead>
          <TableHead>Kind</TableHead>
          <TableHead>Price</TableHead>
          <TableHead>Turnaround</TableHead>
          <TableHead>Components</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="font-mono text-xs">
              {item.id}
              <div>
                {item.active ? null : <Badge tone="muted">inactive</Badge>}
                <span className="ml-1 text-muted-foreground">since v{item.since_version}</span>
              </div>
            </TableCell>
            <TableCell>
              <div className="font-medium">{item.name}</div>
              {item.synonyms.length > 0 ? <div className="text-xs text-muted-foreground">{item.synonyms.join(" · ")}</div> : null}
              {item.category ? <div className="text-xs text-muted-foreground">Category: {item.category}</div> : null}
            </TableCell>
            <TableCell>{item.kind}</TableCell>
            <TableCell className="whitespace-nowrap">
              {item.kind === "test" ? (
                <>
                  {formatPrice(item.price_inr)}
                  {item.price_source ? <div className="text-xs text-muted-foreground">{item.price_source}</div> : null}
                </>
              ) : (
                "—"
              )}
            </TableCell>
            <TableCell className="whitespace-nowrap">
              {item.kind === "test" ? formatTurnaround(item.tat_minutes) : "—"}
              {item.invasive ? <Badge tone="warning" className="ml-1">invasive</Badge> : null}
            </TableCell>
            <TableCell className="text-xs">
              {item.components && item.components.length > 0
                ? item.components.map((c) => `${c.name}${c.unit ? ` (${c.unit})` : ""}`).join(", ")
                : "—"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export function ComponentTable({ rows }: { rows: ComponentRow[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Id</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Unit</TableHead>
          <TableHead>Reference ranges</TableHead>
          <TableHead>Normal text</TableHead>
          <TableHead>Tests</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((c) => {
          const ranges = formatRefRanges(c.ref_ranges, c.unit_si);
          return (
            <TableRow key={c.id}>
              <TableCell className="font-mono text-xs">{c.id}</TableCell>
              <TableCell>
                {c.name}
                {c.loinc ? <div className="text-xs text-muted-foreground">LOINC {c.loinc}</div> : null}
              </TableCell>
              <TableCell className="whitespace-nowrap">
                {c.unit_si ?? "—"}
                {c.unit_conv ? <div className="text-xs text-muted-foreground">{c.unit_conv} (× {c.conv_factor ?? "?"})</div> : null}
              </TableCell>
              <TableCell className="text-xs">
                {ranges.length === 0 ? "—" : ranges.map((line) => <div key={line}>{line}</div>)}
              </TableCell>
              <TableCell className="text-xs">{c.normal_text ?? "—"}</TableCell>
              <TableCell><List items={c.tests} /></TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
