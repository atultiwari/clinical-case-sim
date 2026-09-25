import { prettyJson } from "@/lib/ground-truth";

export function JsonBlock({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span className="text-muted-foreground">—</span>;
  return (
    <pre className="max-h-96 overflow-auto rounded-md bg-muted p-2 font-mono text-xs whitespace-pre-wrap">
      {prettyJson(value)}
    </pre>
  );
}
