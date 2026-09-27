import type { ChartEntry } from "@nidana/contracts/api";
import { useState, type ReactNode } from "react";
import { Pressable, Text, View } from "react-native";
import {
  blocksByDay,
  carriedLabel,
  displayValue,
  trendOf,
  type ResultTable,
  type Units,
} from "@/lib/chart";
import { StatusBadge, Tabs } from "./ui";

/**
 * The Chart (SPEC §5.3): a clinical timeline, one card per simulated day, one row per event with
 * its time on the left; results from one order form a table with trends for serial values.
 */

interface Selection {
  readonly selected: readonly string[];
  readonly onToggle: (ref: string) => void;
}

const pad = (n: number): string => String(n).padStart(2, "0");
const timeOf = (minutes: number): string =>
  `${pad(Math.floor((minutes % 1440) / 60))}:${pad(minutes % 60)}`;

function SelectBox({
  entryRef,
  label,
  selection,
}: {
  readonly entryRef: string;
  /** Read out by screen readers and used by the Android test: "Cite Blood lead". */
  readonly label: string;
  readonly selection?: Selection;
}) {
  if (selection === undefined) return null;
  const on = selection.selected.includes(entryRef);
  return (
    <Pressable
      testID={`cite-${entryRef}`}
      accessibilityRole="checkbox"
      accessibilityState={{ checked: on }}
      accessibilityLabel={`Cite ${label}`}
      hitSlop={12}
      onPress={() => selection.onToggle(entryRef)}
      className={`mt-0.5 h-5 w-5 items-center justify-center rounded border ${on ? "border-brand bg-brand" : "border-line bg-white"}`}
    >
      {on ? <Text className="text-[11px] font-bold text-white">✓</Text> : null}
    </Pressable>
  );
}

const KIND_LABEL: Record<ChartEntry["kind"], string> = {
  vignette: "Presentation",
  history: "History",
  exam: "Exam",
  result: "Result",
  report: "Report",
  consult: "Consult",
  no_record: "No record",
};

const KIND_TONE: Partial<Record<ChartEntry["kind"], string>> = {
  history: "text-brand",
  exam: "text-teal-700",
  report: "text-purple-700",
  consult: "text-indigo-700",
};

/** One timeline row: time and kind on the left, content on the right. */
function Row({
  at,
  kind,
  title,
  children,
}: {
  readonly at: number;
  readonly kind: ChartEntry["kind"];
  readonly title: string | null;
  readonly children: ReactNode;
}) {
  return (
    <View className="flex-row gap-3 border-t border-line/70 px-3 py-2.5">
      <View className="w-16">
        <Text className="font-mono text-xs text-muted">{timeOf(at)}</Text>
        <Text
          className={`text-[10px] font-semibold uppercase tracking-wider ${KIND_TONE[kind] ?? "text-muted"}`}
        >
          {KIND_LABEL[kind]}
        </Text>
      </View>
      <View className="flex-1 gap-1">
        {title ? (
          <Text className="text-sm font-semibold text-ink">{title}</Text>
        ) : null}
        {children}
      </View>
    </View>
  );
}

function EntryRow({
  entry,
  selection,
}: {
  readonly entry: ChartEntry;
  readonly selection?: Selection;
}) {
  return (
    <View testID={`entry-${entry.ref}`}>
      <Row at={entry.at} kind={entry.kind} title={entry.itemName}>
        <View className="flex-row gap-2">
          <SelectBox
            entryRef={entry.ref}
            label={entry.itemName ?? entry.text ?? "this entry"}
            selection={selection}
          />
          <View className="flex-1 gap-1">
            {entry.report ? (
              <>
                <View className="flex-row flex-wrap items-center gap-2">
                  <StatusBadge status={entry.report.status} />
                </View>
                {entry.report.statusLine ? (
                  <Text
                    testID="status-line"
                    className="rounded bg-amber-50 px-2 py-1 text-xs italic text-provisional"
                  >
                    {entry.report.statusLine}
                  </Text>
                ) : null}
                {entry.report.text ? (
                  <Text className="text-sm leading-5 text-ink">
                    {entry.report.text}
                  </Text>
                ) : null}
                {entry.report.impression ? (
                  <Text className="text-sm font-medium text-ink">
                    Impression: {entry.report.impression}
                  </Text>
                ) : null}
              </>
            ) : null}
            {entry.text ? (
              <Text
                className={`text-sm leading-5 text-ink ${entry.kind === "history" ? "italic" : ""}`}
              >
                {entry.kind === "history" ? `“${entry.text}”` : entry.text}
              </Text>
            ) : null}
            {entry.kind === "no_record" ? (
              <Text className="text-sm text-muted">
                Nothing further recorded.
              </Text>
            ) : null}
            {entry.recommendations.map((r) => (
              <Text key={r} className="text-sm leading-5 text-ink">
                • {r}
              </Text>
            ))}
          </View>
        </View>
      </Row>
    </View>
  );
}

function Trend({
  entries,
  component,
}: {
  readonly entries: readonly ChartEntry[];
  readonly component: string;
}) {
  const points = trendOf(entries, component);
  if (points.length < 2) return null;
  return (
    <Text testID={`trend-${component}`} className="text-[11px] text-muted">
      {points.map((p) => `d${p.day} ${p.value}`).join("  →  ")}
    </Text>
  );
}

function ResultsRow({
  table,
  units,
  all,
  selection,
}: {
  readonly table: ResultTable;
  readonly units: Units;
  readonly all: readonly ChartEntry[];
  readonly selection?: Selection;
}) {
  return (
    <View testID={`results-${table.item}`}>
      <Row at={table.at} kind="result" title={table.itemName}>
        {table.requestedDay !== null ? (
          <Text className="text-[11px] text-muted">
            Ordered on day {table.requestedDay}
          </Text>
        ) : null}
        <View className="mt-1 rounded-md border border-line/70">
          {table.rows.map(({ entry, name }, i) => {
            const border = i === 0 ? "" : "border-t border-line/50";
            if (entry.value === null) {
              return (
                <View
                  key={entry.ref}
                  className={`flex-row gap-2 px-2 py-1.5 ${border}`}
                >
                  <SelectBox
                    entryRef={entry.ref}
                    label={name}
                    selection={selection}
                  />
                  <Text className="flex-1 text-sm text-ink">
                    {name}: {entry.text ?? "—"}
                  </Text>
                </View>
              );
            }
            const shown = displayValue(entry.value, units);
            const carried = carriedLabel(entry);
            const abnormal = shown.flag !== null && shown.flag !== "";
            return (
              <View
                key={entry.ref}
                testID={`value-${entry.component?.id}`}
                className={`gap-0.5 px-2 py-1.5 ${border} ${abnormal ? "bg-red-50/60" : ""}`}
              >
                <View className="flex-row items-center gap-2">
                  <SelectBox
                    entryRef={entry.ref}
                    label={name}
                    selection={selection}
                  />
                  <Text className="flex-1 text-sm text-ink">{name}</Text>
                  <Text
                    className={`font-mono text-sm font-semibold ${abnormal ? "text-danger" : "text-ink"}`}
                  >
                    {shown.text}
                    {abnormal ? ` ${shown.flag}` : ""}
                  </Text>
                  <Text className="w-20 text-xs text-muted">
                    {shown.unit ?? ""}
                  </Text>
                </View>
                <View className="flex-row flex-wrap gap-x-3 pl-7">
                  {shown.refRange ? (
                    <Text className="text-[11px] text-muted">
                      ref {shown.refRange}
                    </Text>
                  ) : null}
                  {carried ? (
                    <Text
                      testID="carried"
                      className="text-[11px] font-medium text-provisional"
                    >
                      {carried}
                    </Text>
                  ) : null}
                  {entry.component ? (
                    <Trend entries={all} component={entry.component.id} />
                  ) : null}
                </View>
              </View>
            );
          })}
        </View>
      </Row>
    </View>
  );
}

function Presentation({
  entries,
  selection,
}: {
  readonly entries: readonly ChartEntry[];
  readonly selection?: Selection;
}) {
  if (entries.length === 0) return null;
  return (
    <View
      testID="presentation"
      className="gap-1.5 rounded-xl border border-line bg-white p-3"
    >
      <Text className="text-[10px] font-semibold uppercase tracking-wider text-muted">
        Presentation
      </Text>
      {entries.map((e) => (
        <View key={e.ref} testID={`entry-${e.ref}`} className="flex-row gap-2">
          <SelectBox
            entryRef={e.ref}
            label={e.text ?? "this finding"}
            selection={selection}
          />
          <Text className="flex-1 text-sm text-ink">{e.text}</Text>
        </View>
      ))}
    </View>
  );
}

export function ChartView({
  entries,
  selection,
  showPresentation = false,
}: {
  readonly entries: readonly ChartEntry[];
  readonly selection?: Selection;
  /** The presentation facts; the workspace shows them in the case summary instead. */
  readonly showPresentation?: boolean;
}) {
  const [units, setUnits] = useState<Units>("si");
  const presentation = entries.filter((e) => e.kind === "vignette");
  const days = blocksByDay(entries.filter((e) => e.kind !== "vignette"));
  return (
    <View testID="chart" className="gap-3">
      <View className="flex-row flex-wrap items-center justify-between gap-2">
        <Text className="text-base font-semibold text-ink">Chart</Text>
        <Tabs
          testID="units"
          value={units}
          onChange={setUnits}
          options={[
            { value: "si", label: "SI" },
            { value: "conventional", label: "Conventional" },
          ]}
        />
      </View>
      {showPresentation ? (
        <Presentation entries={presentation} selection={selection} />
      ) : null}
      {days.length === 0 ? (
        <Text className="text-sm text-muted">
          Nothing in the Chart yet: ask, examine or order to begin.
        </Text>
      ) : null}
      {days.map(({ day, blocks }) => (
        <View
          key={day}
          className="overflow-hidden rounded-xl border border-line bg-white"
        >
          <View className="flex-row items-baseline justify-between bg-slate-50 px-3 py-2">
            <Text className="text-sm font-semibold text-ink">Day {day}</Text>
            <Text className="text-[11px] text-muted">
              {blocks.length} {blocks.length === 1 ? "event" : "events"}
            </Text>
          </View>
          {blocks.map((block) =>
            block.type === "entry" ? (
              <EntryRow
                key={block.entry.ref}
                entry={block.entry}
                selection={selection}
              />
            ) : (
              <ResultsRow
                key={`${block.table.item}-${block.table.at}`}
                table={block.table}
                units={units}
                all={entries}
                selection={selection}
              />
            ),
          )}
        </View>
      ))}
    </View>
  );
}
