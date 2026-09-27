import type { ReportContent } from "@nidana/contracts/api";
import { useLocalSearchParams, Link } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { Text, View } from "react-native";
import {
  Button,
  Card,
  ErrorNote,
  Heading,
  Loading,
  Muted,
  Screen,
  StatusBadge,
} from "@/components/ui";
import { formatClock, formatInr } from "@/lib/format";
import { useApi } from "@/lib/game";
import { useLoad } from "@/lib/use-load";

/** The debrief (SPEC §5.13): score, harm, paths, what was synthetic, both report versions, and the source. */

const SYNTHETIC = new Set(["affected", "normal", "rule", "reviewer"]);

function Points({
  label,
  value,
  of,
}: {
  readonly label: string;
  readonly value: number;
  readonly of: number;
}) {
  return (
    <View className="gap-1">
      <View className="flex-row justify-between">
        <Text className="text-sm text-slate-200">{label}</Text>
        <Text className="font-mono text-sm text-white">
          {value.toFixed(1)} / {of}
        </Text>
      </View>
      <View className="h-1 overflow-hidden rounded-full bg-white/15">
        <View
          className="h-full rounded-full bg-sky-300"
          style={{ width: `${Math.round((value / of) * 100)}%` }}
        />
      </View>
    </View>
  );
}

function Report({
  label,
  report,
}: {
  readonly label: string;
  readonly report: ReportContent;
}) {
  return (
    <View className="flex-1 gap-1 rounded-lg border border-line bg-white p-3">
      <Text className="text-xs uppercase tracking-wide text-muted">
        {label}
      </Text>
      <StatusBadge status={report.status} />
      {report.text ? (
        <Text className="text-sm text-ink">{report.text}</Text>
      ) : null}
      {report.impression ? (
        <Text className="text-sm font-medium text-ink">
          Impression: {report.impression}
        </Text>
      ) : null}
    </View>
  );
}

export default function Debrief() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const api = useApi();
  const { data: debrief, error } = useLoad(
    () => api.debrief(id),
    [api, id],
    "Could not load the debrief",
  );

  if (debrief === null)
    return error ? <ErrorNote message={error} /> : <Loading label="Scoring…" />;
  const { score } = debrief;
  const synthetic = Object.values(debrief.origins).filter((o) =>
    SYNTHETIC.has(o),
  ).length;
  const released = Object.keys(debrief.origins).length;

  return (
    <Screen>
      <View testID="score" className="gap-3 rounded-2xl bg-ink p-5">
        <View className="flex-row items-end gap-3">
          <Text testID="total" className="text-5xl font-bold text-white">
            {Math.round(score.total)}
          </Text>
          <Text className="pb-2 text-sm text-slate-300">out of 100</Text>
        </View>
        <View className="gap-1.5">
          <Points
            label={`Diagnosis (anchor ${score.diagnosis.anchor} of 5)`}
            value={score.diagnosis.points}
            of={40}
          />
          <Points
            label={`Management (${score.management.met} of ${score.management.scorable} must-dos)`}
            value={score.management.points}
            of={30}
          />
          <Points label="Efficiency" value={score.efficiency.points} of={20} />
          <Points label="Reasoning" value={score.reasoning.points} of={10} />
        </View>
      </View>

      {score.safety.violations.length > 0 ? (
        <Card testID="harm">
          <Text className="text-base font-semibold text-danger">
            You harmed the patient
          </Text>
          {score.safety.violations.map((v) => (
            <Text key={v.text} className="text-sm text-danger">
              • {v.text}
            </Text>
          ))}
          {score.safety.capApplied ? (
            <Muted>
              The total is capped at 50 and loses 15 points for each.
            </Muted>
          ) : null}
        </Card>
      ) : null}

      <Card testID="diagnosis">
        <Heading>{debrief.finalDiagnosis.name}</Heading>
        <Muted>Your diagnosis: {debrief.committed.dx.name}</Muted>
        {score.diagnosis.text ? <Muted>{score.diagnosis.text}</Muted> : null}
      </Card>

      <Card testID="must-do">
        <Heading>Must do</Heading>
        {score.mustDo.map((m) => (
          <Text
            key={m.text}
            className={`text-sm ${m.met ? "text-final" : "text-danger"}`}
          >
            {m.met ? "✓" : "✗"} {m.text}
          </Text>
        ))}
      </Card>

      <Card testID="paths">
        <Heading>Your path and the efficient path</Heading>
        <Muted>
          You spent {formatInr(debrief.paths.spend)} and committed at{" "}
          {formatClock(debrief.committed.at)}; the efficient path&apos;s tests
          cost {formatInr(debrief.paths.efficientCost)}.
        </Muted>
        {debrief.paths.efficient.map((p) => (
          <Text
            key={p.id}
            className={`text-sm ${p.done ? "text-ink" : "text-muted"}`}
          >
            {p.done ? "✓" : "–"} {p.name}
          </Text>
        ))}
      </Card>

      <Card testID="synthetic">
        <Heading>Which results were synthetic</Heading>
        <Muted>
          {synthetic} of {released} items you saw were generated for this case
          from the true diagnosis and reviewed; the rest come from the article.
        </Muted>
      </Card>

      {debrief.reports.map((r) => (
        <Card key={r.test} testID="report-pair">
          <Heading>{r.testName}: first report and after review</Heading>
          <View className="flex-row flex-wrap gap-2">
            <Report label="As first issued" report={r.provisional} />
            {r.final ? (
              <Report label="After expert review" report={r.final} />
            ) : null}
          </View>
          {!r.finalSeen ? (
            <Muted>You did not request the review during the case.</Muted>
          ) : null}
        </Card>
      ))}

      {debrief.keyDiscriminators.length > 0 ? (
        <Card testID="discriminators">
          <Heading>Key discriminators</Heading>
          {debrief.keyDiscriminators.map((k) => (
            <Text key={k} className="text-sm text-ink">
              • {k}
            </Text>
          ))}
        </Card>
      ) : null}

      {debrief.teachingPoints.length > 0 ? (
        <Card testID="teaching">
          <Heading>Teaching points</Heading>
          {debrief.teachingPoints.map((t) => (
            <Text key={t} className="text-sm text-ink">
              • {t}
            </Text>
          ))}
        </Card>
      ) : null}

      {debrief.source ? (
        <Card testID="source">
          <Heading>Source</Heading>
          {debrief.source.citation ? (
            <Text className="text-sm text-ink">{debrief.source.citation}</Text>
          ) : null}
          <Muted>
            Licence: {debrief.source.licence}
            {debrief.source.attribution
              ? `. ${debrief.source.attribution}`
              : ""}
          </Muted>
          {debrief.source.url && /^https?:\/\//i.test(debrief.source.url) ? (
            <Button
              label="Read the article"
              variant="secondary"
              onPress={() =>
                void WebBrowser.openBrowserAsync(debrief.source?.url ?? "")
              }
            />
          ) : null}
        </Card>
      ) : null}

      <Link href="/" asChild>
        <Button
          testID="home"
          label="Back to the cases"
          onPress={() => undefined}
        />
      </Link>
    </Screen>
  );
}
