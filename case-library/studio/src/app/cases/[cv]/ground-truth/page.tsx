import { Empty, Fields, Section } from "@/components/common";
import { JsonBlock } from "@/components/json-block";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { conditionItems, diagnosisLabel, parseRubric, type ConditionItem } from "@/lib/ground-truth";
import { loadCase, type CaseParams } from "@/server/case-page";
import { getGroundTruth, listTestUtility } from "@/server/queries/ground-truth";

export default async function GroundTruthPage({ params }: { params: CaseParams }) {
  const c = await loadCase(params);
  const [gt, utility] = await Promise.all([getGroundTruth(c.id), listTestUtility(c.id)]);
  if (!gt) return <Empty>No ground truth yet.</Empty>;
  const dx = diagnosisLabel(gt.final_dx);
  const rubric = parseRubric(gt.rubric);
  return (
    <>
      <Section title="Diagnosis">
        <p className="mb-2 text-base font-semibold">
          {dx.text} {dx.id ? <span className="font-mono text-sm text-muted-foreground">{dx.id}</span> : null}
        </p>
        <Fields
          rows={[
            ["Final diagnosis (JSON)", <JsonBlock key="dx" value={gt.final_dx} />],
            ["Accepted differential", <JsonBlock key="ad" value={gt.accepted_differential} />],
            ["Red herrings", <JsonBlock key="rh" value={gt.red_herrings} />],
            ["Key discriminators", <JsonBlock key="kd" value={gt.key_discriminators} />],
            ["Treatment given", gt.treatment_given],
            ["Outcome", gt.outcome],
          ]}
        />
      </Section>
      <Section title="Rubric anchors" aside={rubric.defaultScore !== null ? `default score ${rubric.defaultScore}` : undefined}>
        {rubric.unparsed !== null ? <JsonBlock value={rubric.unparsed} /> : null}
        {rubric.anchors.length === 0 && rubric.unparsed === null ? <Empty>No rubric.</Empty> : null}
        {rubric.anchors.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-16">Score</TableHead>
                <TableHead>Anchor</TableHead>
                <TableHead>Condition</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rubric.anchors.map((anchor, index) => (
                <TableRow key={index}>
                  <TableCell className="font-semibold">{anchor.score ?? "—"}</TableCell>
                  <TableCell>{anchor.text}</TableCell>
                  <TableCell className="w-1/2"><JsonBlock value={anchor.condition} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : null}
      </Section>
      <ConditionTable title="Must do" items={conditionItems(gt.must_do)} />
      <ConditionTable title="Must not do" items={conditionItems(gt.must_not_do)} />
      <Section title="Efficient path and teaching points">
        <Fields
          rows={[
            ["Efficient path", <JsonBlock key="ep" value={gt.efficient_path} />],
            ["Teaching points", <JsonBlock key="tp" value={gt.teaching_points} />],
          ]}
        />
      </Section>
      <Section title="Test utility" aside={`${utility.length} tests`}>
        {utility.length === 0 ? (
          <Empty>No test utility rows.</Empty>
        ) : (
          <Table>
            <TableBody>
              {utility.map((u) => (
                <TableRow key={u.test_item_id}>
                  <TableCell className="font-mono text-xs">{u.test_item_id}</TableCell>
                  <TableCell>{u.test_name ?? "—"}</TableCell>
                  <TableCell><Badge tone={u.utility === "risky" ? "danger" : u.utility === "essential" ? "success" : "neutral"}>{u.utility.replace("_", " ")}</Badge></TableCell>
                  <TableCell className="text-xs">{u.rationale ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Section>
    </>
  );
}

function ConditionTable({ title, items }: { title: string; items: ConditionItem[] }) {
  return (
    <Section title={title} aside={`${items.length} items`}>
      {items.length === 0 ? (
        <Empty>None.</Empty>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Item</TableHead>
              <TableHead>Condition</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item, index) => (
              <TableRow key={index}>
                <TableCell>{item.text}</TableCell>
                <TableCell className="w-1/2"><JsonBlock value={item.condition} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Section>
  );
}
