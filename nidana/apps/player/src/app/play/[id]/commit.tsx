import type { SearchItem } from "@nidana/contracts/api";
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";
import { ChartView } from "@/components/chart";
import {
  Button,
  Card,
  ErrorNote,
  Loading,
  Muted,
  Screen,
} from "@/components/ui";
import {
  MAX_EVIDENCE,
  commitProblems,
  movePlanItem,
  toggleEvidence,
} from "@/lib/commit";
import { nameOf, useApi, useCatalogue, useMissingReport } from "@/lib/game";
import { useLoad } from "@/lib/use-load";
import { searchItems, type SearchKind } from "@/lib/search";

/** The commit (SPEC §5.12): diagnosis, up to five items of key evidence, and a plan in order. */

function Picker({
  encounterId,
  items,
  kinds,
  placeholder,
  testID,
  onPick,
}: {
  readonly encounterId: string;
  readonly items: readonly SearchItem[];
  /** The first kind is the one a search with no match is reported as. */
  readonly kinds: readonly [SearchKind, ...SearchKind[]];
  readonly placeholder: string;
  readonly testID: string;
  readonly onPick: (item: SearchItem) => void;
}) {
  const [query, setQuery] = useState("");
  const found = searchItems(items, kinds, query, 8);
  useMissingReport(encounterId, kinds[0], query, found.length);
  return (
    <View className="gap-1.5">
      <TextInput
        testID={testID}
        value={query}
        onChangeText={setQuery}
        placeholder={placeholder}
        autoCorrect={false}
        autoCapitalize="none"
        className="rounded-lg border border-line bg-white px-3 py-2 text-ink"
      />
      {query.trim().length >= 2 && found.length === 0 ? (
        <Text testID="no-match" className="text-sm text-muted">
          No match in the catalogue.
        </Text>
      ) : null}
      {found.map((item) => (
        <Pressable
          key={item.id}
          testID={`pick-${item.id}`}
          accessibilityRole="button"
          onPress={() => {
            onPick(item);
            setQuery("");
          }}
          className="rounded-lg border border-line bg-white px-3 py-2"
        >
          <Text className="text-sm text-ink">{item.name}</Text>
        </Pressable>
      ))}
    </View>
  );
}

export default function Commit() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const api = useApi();
  const { items } = useCatalogue();
  const { data: view, error: loadError } = useLoad(
    () => api.view(id),
    [api, id],
    "Could not load the encounter",
  );
  const [dx, setDx] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<readonly string[]>([]);
  const [plan, setPlan] = useState<readonly string[]>([]);
  const [note, setNote] = useState("");
  const [sendError, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const error = sendError ?? loadError;

  if (view === null || items === null)
    return error ? <ErrorNote message={error} /> : <Loading />;
  const problems = commitProblems({ dx, evidence, plan });

  const submit = async () => {
    if (dx === null) return;
    setSending(true);
    setError(null);
    try {
      await api.commit(id, {
        dx,
        evidence,
        plan,
        ...(note.trim() ? { note: note.trim() } : {}),
      });
      router.replace(`/play/${id}/debrief`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "The commit was not recorded");
      setSending(false);
    }
  };

  return (
    <Screen>
      <ErrorNote message={error} />
      <Card testID="commit-dx">
        <Text className="text-base font-semibold text-ink">
          Final diagnosis
        </Text>
        {dx ? (
          <View className="flex-row items-center gap-2">
            <Text
              testID="chosen-dx"
              className="flex-1 text-sm font-medium text-ink"
            >
              {nameOf(items, dx)}
            </Text>
            <Button
              label="Change"
              variant="secondary"
              onPress={() => setDx(null)}
            />
          </View>
        ) : (
          <Picker
            encounterId={id}
            items={items}
            kinds={["diagnosis"]}
            placeholder="Search diagnoses"
            testID="dx-search"
            onPick={(i) => setDx(i.id)}
          />
        )}
      </Card>

      <Card testID="commit-plan">
        <Text className="text-base font-semibold text-ink">Plan</Text>
        <Muted>Actions and referrals, in the order they should happen.</Muted>
        {plan.map((itemId, index) => (
          <View
            key={itemId}
            testID={`plan-${itemId}`}
            className="flex-row items-center gap-1.5"
          >
            <Text className="flex-1 text-sm text-ink">
              {index + 1}. {nameOf(items, itemId)}
            </Text>
            <Button
              label="↑"
              accessibilityLabel={`Move ${nameOf(items, itemId)} up`}
              variant="secondary"
              onPress={() => setPlan(movePlanItem(plan, index, -1))}
            />
            <Button
              label="↓"
              accessibilityLabel={`Move ${nameOf(items, itemId)} down`}
              variant="secondary"
              onPress={() => setPlan(movePlanItem(plan, index, 1))}
            />
            <Button
              label="✕"
              accessibilityLabel={`Remove ${nameOf(items, itemId)}`}
              variant="secondary"
              onPress={() => setPlan(plan.filter((p) => p !== itemId))}
            />
          </View>
        ))}
        <Picker
          encounterId={id}
          items={items}
          kinds={["action", "referral"]}
          placeholder="Search actions and referrals"
          testID="plan-search"
          onPick={(i) => setPlan(plan.includes(i.id) ? plan : [...plan, i.id])}
        />
      </Card>

      <Card testID="commit-note">
        <Text className="text-base font-semibold text-ink">
          Reasoning (optional)
        </Text>
        <TextInput
          testID="note"
          value={note}
          onChangeText={setNote}
          multiline
          maxLength={2000}
          placeholder="Stored with your commit; not scored yet."
          className="min-h-20 rounded-lg border border-line bg-white px-3 py-2 text-ink"
        />
      </Card>

      <View className="gap-2">
        <Text className="text-base font-semibold text-ink">
          Key evidence ({evidence.length}/{MAX_EVIDENCE})
        </Text>
        <Muted>
          Tick up to five items in the Chart that support your diagnosis.
        </Muted>
        <ChartView
          showPresentation
          entries={view.chart.filter((e) => e.kind !== "no_record")}
          selection={{
            selected: evidence,
            onToggle: (ref) => setEvidence(toggleEvidence(evidence, ref)),
          }}
        />
      </View>

      {problems.map((p) => (
        <Text key={p} className="text-sm text-danger">
          {p}
        </Text>
      ))}
      <Button
        testID="submit-commit"
        label={sending ? "Committing…" : "Commit and see the debrief"}
        disabled={sending || problems.length > 0}
        onPress={submit}
      />
    </Screen>
  );
}
