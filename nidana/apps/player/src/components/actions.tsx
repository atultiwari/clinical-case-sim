import type {
  ActionRequest,
  PlayerView,
  SearchItem,
} from "@nidana/contracts/api";
import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";
import { formatClock, formatDuration, formatInr } from "@/lib/format";
import { nameOf } from "@/lib/game";
import { searchItems, type SearchKind } from "@/lib/search";
import { Button, Muted, Tabs } from "./ui";

/** The action panel (SPEC §5.3): Ask, Examine, Order, Refer, Differential, Wait and Commit. */

type Mode =
  "ask" | "examine" | "order" | "refer" | "differential" | "wait" | "commit";

const MODES: readonly { readonly value: Mode; readonly label: string }[] = [
  { value: "ask", label: "Ask" },
  { value: "examine", label: "Examine" },
  { value: "order", label: "Order" },
  { value: "refer", label: "Refer" },
  { value: "differential", label: "Differential" },
  { value: "wait", label: "Wait" },
  { value: "commit", label: "Commit" },
];

const KIND_OF: Record<
  "ask" | "examine" | "order" | "refer" | "differential",
  SearchKind
> = {
  ask: "history",
  examine: "exam",
  order: "test",
  refer: "referral",
  differential: "diagnosis",
};

const PLACEHOLDER: Record<
  "ask" | "examine" | "order" | "refer" | "differential",
  string
> = {
  ask: "Search questions, e.g. medicines",
  examine: "Search examinations, e.g. pallor",
  order: "Search tests, e.g. blood count",
  refer: "Search specialties, e.g. haematology",
  differential: "Search diagnoses",
};

export function GameStatus({ view }: { readonly view: PlayerView }) {
  const used = Math.min(1, view.spend / Math.max(1, view.limits.budget));
  return (
    <View
      testID="status"
      className="gap-2 rounded-xl border border-line bg-white px-4 py-3"
    >
      <View className="flex-row flex-wrap items-end gap-x-6 gap-y-2">
        <View>
          <Text className="text-[10px] font-semibold uppercase tracking-wider text-muted">
            Clock
          </Text>
          <Text
            testID="clock"
            className="font-mono text-lg font-semibold text-ink"
          >
            {formatClock(view.clock)}
          </Text>
        </View>
        <View className="min-w-40 flex-1 gap-1">
          <Text testID="spend" className="text-xs text-ink">
            Spent {formatInr(view.spend)} of {formatInr(view.limits.budget)}
          </Text>
          <View className="h-1.5 overflow-hidden rounded-full bg-slate-100">
            <View
              className={`h-full rounded-full ${used > 0.85 ? "bg-danger" : "bg-brand"}`}
              style={{ width: `${Math.round(used * 100)}%` }}
            />
          </View>
        </View>
        <Text className="text-xs text-ink">
          Referrals {view.limits.referralsUsed} of{" "}
          {view.limits.referralsAllowed}
        </Text>
      </View>
      {view.pending.length > 0 ? (
        <View testID="pending" className="flex-row flex-wrap gap-1.5">
          {view.pending.map((p) => (
            <Text
              key={`${p.item}-${p.orderedAt}`}
              className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-muted"
            >
              {p.itemName ?? p.item} · due {formatClock(p.dueAt)}
            </Text>
          ))}
        </View>
      ) : null}
      {view.mustCommit !== null ? (
        <Text testID="must-commit" className="text-sm font-medium text-danger">
          The maximum stay has been reached. Commit to a diagnosis and plan.
        </Text>
      ) : null}
    </View>
  );
}

function ResultRow({
  item,
  onPress,
}: {
  readonly item: SearchItem;
  readonly onPress: () => void;
}) {
  const cost =
    item.kind === "test"
      ? `${formatInr(item.priceInr ?? 0)} · result in ${formatDuration(item.turnaroundMinutes ?? 0)}`
      : null;
  return (
    <Pressable
      testID={`pick-${item.id}`}
      accessibilityRole="button"
      accessibilityLabel={item.name}
      onPress={onPress}
      className="rounded-lg border border-line bg-white px-3 py-2"
    >
      <Text className="text-sm text-ink">{item.name}</Text>
      {cost ? <Text className="text-xs text-muted">{cost}</Text> : null}
    </Pressable>
  );
}

interface SearchProps {
  readonly items: readonly SearchItem[];
  readonly kind: SearchKind;
  readonly placeholder: string;
  readonly onPick: (item: SearchItem) => void;
}

function Search({ items, kind, placeholder, onPick }: SearchProps) {
  const [query, setQuery] = useState("");
  const found = searchItems(items, [kind], query);
  return (
    <View className="gap-2">
      <TextInput
        testID="search"
        value={query}
        onChangeText={setQuery}
        placeholder={placeholder}
        autoCorrect={false}
        autoCapitalize="none"
        className="rounded-lg border border-line bg-white px-3 py-2 text-ink"
      />
      {query.trim().length >= 2 && found.length === 0 ? (
        <Text testID="no-match" className="text-sm text-muted">
          No match in the catalogue. Try another word or a synonym.
        </Text>
      ) : null}
      {found.map((item) => (
        <ResultRow
          key={item.id}
          item={item}
          onPress={() => {
            onPick(item);
            setQuery("");
          }}
        />
      ))}
    </View>
  );
}

function Confirm({
  item,
  mode,
  onConfirm,
  onCancel,
}: {
  readonly item: SearchItem;
  readonly mode: "order" | "refer";
  readonly onConfirm: () => void;
  readonly onCancel: () => void;
}) {
  const detail =
    mode === "order"
      ? `Costs ${formatInr(item.priceInr ?? 0)}; the result arrives in ${formatDuration(item.turnaroundMinutes ?? 0)}.`
      : "The consult note arrives in 4 hours.";
  return (
    <View
      testID="confirm-card"
      className="gap-2 rounded-lg border border-brand bg-blue-50 p-3"
    >
      <Text className="text-sm font-medium text-ink">{item.name}</Text>
      <Muted>{detail}</Muted>
      <View className="flex-row gap-2">
        <Button
          testID="confirm"
          label={mode === "order" ? "Order" : "Refer"}
          onPress={onConfirm}
        />
        <Button
          testID="cancel"
          label="Cancel"
          variant="secondary"
          onPress={onCancel}
        />
      </View>
    </View>
  );
}

function DifferentialEditor({
  view,
  items,
  onSave,
}: {
  readonly view: PlayerView;
  readonly items: readonly SearchItem[];
  readonly onSave: (list: readonly string[]) => void;
}) {
  const [list, setList] = useState<readonly string[]>(
    view.differential.at(-1)?.items ?? [],
  );
  return (
    <View className="gap-2">
      <Muted>
        Most likely first. Optional; the debrief shows how it changed.
      </Muted>
      {list.map((id, index) => (
        <View key={id} className="flex-row items-center gap-2">
          <Text className="flex-1 text-sm text-ink">
            {index + 1}. {nameOf(items, id)}
          </Text>
          <Button
            label="Remove"
            variant="secondary"
            onPress={() => setList(list.filter((x) => x !== id))}
          />
        </View>
      ))}
      <Search
        items={items}
        kind="diagnosis"
        placeholder={PLACEHOLDER.differential}
        onPick={(item) =>
          setList(
            list.includes(item.id) ? list : [...list, item.id].slice(0, 10),
          )
        }
      />
      <Button
        testID="save-differential"
        label="Save differential"
        disabled={list.length === 0}
        onPress={() => onSave(list)}
      />
    </View>
  );
}

export function ActionPanel({
  view,
  items,
  busy,
  onAct,
  onCommit,
}: {
  readonly view: PlayerView;
  readonly items: readonly SearchItem[];
  readonly busy: boolean;
  readonly onAct: (action: ActionRequest) => void;
  readonly onCommit: () => void;
}) {
  const [mode, setMode] = useState<Mode>("ask");
  const [selected, setSelected] = useState<SearchItem | null>(null);
  const locked = view.mustCommit !== null || view.status === "committed";
  const toNextDay = (Math.floor(view.clock / 1440) + 1) * 1440 - view.clock;

  const body = (() => {
    if (locked && mode !== "commit") {
      return <Muted>Only the commit is open now.</Muted>;
    }
    switch (mode) {
      case "ask":
      case "examine":
        return (
          <Search
            items={items}
            kind={KIND_OF[mode]}
            placeholder={PLACEHOLDER[mode]}
            onPick={(item) => onAct({ kind: mode, item: item.id })}
          />
        );
      case "order":
      case "refer":
        return selected === null ? (
          <Search
            items={items}
            kind={KIND_OF[mode]}
            placeholder={PLACEHOLDER[mode]}
            onPick={setSelected}
          />
        ) : (
          <Confirm
            item={selected}
            mode={mode}
            onCancel={() => setSelected(null)}
            onConfirm={() => {
              onAct({ kind: mode, item: selected.id });
              setSelected(null);
            }}
          />
        );
      case "differential":
        return (
          <DifferentialEditor
            view={view}
            items={items}
            onSave={(list) => onAct({ kind: "differential", items: list })}
          />
        );
      case "wait":
        return (
          <View className="gap-2">
            <Muted>
              Waiting moves the simulated clock; results and notes arrive when
              due.
            </Muted>
            <Button
              testID="wait-next"
              label="Wait for the next result"
              disabled={view.pending.length === 0}
              onPress={() => onAct({ kind: "wait" })}
            />
            <Button
              testID="wait-hour"
              label="Wait one hour"
              variant="secondary"
              onPress={() => onAct({ kind: "wait", minutes: 60 })}
            />
            <Button
              testID="wait-day"
              label="Wait until tomorrow"
              variant="secondary"
              onPress={() => onAct({ kind: "wait", minutes: toNextDay })}
            />
          </View>
        );
      case "commit":
        return (
          <View className="gap-2">
            <Muted>
              Choose the final diagnosis, cite up to five items from the Chart
              and build a plan.
            </Muted>
            <Button
              testID="go-commit"
              label="Go to commit"
              onPress={onCommit}
            />
          </View>
        );
    }
  })();

  return (
    <View
      testID="actions"
      className={`gap-3 ${busy ? "opacity-60" : ""}`}
      pointerEvents={busy ? "none" : "auto"}
    >
      <Tabs
        testID="mode"
        value={mode}
        onChange={(m) => {
          setMode(m);
          setSelected(null);
        }}
        options={MODES}
      />
      {body}
    </View>
  );
}
