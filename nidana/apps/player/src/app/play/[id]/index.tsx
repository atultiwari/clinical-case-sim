import type { ActionRequest, PlayerView } from "@nidana/contracts/api";
import { router, useLocalSearchParams } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { ScrollView, Text, useWindowDimensions, View } from "react-native";
import { ActionPanel, GameStatus } from "@/components/actions";
import { ChartView } from "@/components/chart";
import {
  Card,
  Disclaimer,
  ErrorNote,
  Loading,
  Muted,
  Tabs,
} from "@/components/ui";
import { useApi, useCatalogue } from "@/lib/game";

/** The workspace (SPEC §5.3): the Chart and the action panel; tabs on phones, side by side on wide screens. */

const WIDE = 900;

function CaseIntro({ view }: { readonly view: PlayerView }) {
  return (
    <Card testID="case-intro">
      <Text className="text-lg font-semibold text-ink">{view.case.title}</Text>
      {view.case.vignette ? (
        <Text className="text-sm text-ink">{view.case.vignette}</Text>
      ) : null}
      {view.case.openingStatement ? (
        <Text testID="opening" className="text-sm italic text-muted">
          “{view.case.openingStatement}”
        </Text>
      ) : null}
    </Card>
  );
}

export default function Workspace() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const api = useApi();
  const { items, error: catalogueError } = useCatalogue();
  const { width } = useWindowDimensions();
  const [view, setView] = useState<PlayerView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState<"chart" | "actions">("actions");

  useEffect(() => {
    api.view(id).then(
      (v) => {
        if (v.status === "committed") router.replace(`/play/${id}/debrief`);
        else setView(v);
      },
      (e: unknown) =>
        setError(
          e instanceof Error ? e.message : "Could not load the encounter",
        ),
    );
  }, [api, id]);

  const act = useCallback(
    async (action: ActionRequest) => {
      setBusy(true);
      setError(null);
      try {
        setView(await api.act(id, action));
      } catch (e: unknown) {
        setError(
          e instanceof Error ? e.message : "The action was not recorded",
        );
      } finally {
        setBusy(false);
      }
    },
    [api, id],
  );

  if (view === null) {
    return error ? (
      <View className="p-4">
        <ErrorNote message={error} />
      </View>
    ) : (
      <Loading label="Opening the case…" />
    );
  }

  const chart = (
    <View className="gap-3">
      <CaseIntro view={view} />
      <ChartView entries={view.chart} />
    </View>
  );
  const panel =
    items === null ? (
      catalogueError ? (
        <ErrorNote message={catalogueError} />
      ) : (
        <Loading label="Loading the catalogue…" />
      )
    ) : (
      <ActionPanel
        view={view}
        items={items}
        busy={busy}
        onAct={act}
        onCommit={() => router.push(`/play/${id}/commit`)}
      />
    );
  const wide = width >= WIDE;

  return (
    <View className="flex-1 bg-paper">
      <View className="gap-2 p-3">
        <GameStatus view={view} />
        <ErrorNote message={error} />
        {!wide ? (
          <Tabs
            testID="view"
            value={tab}
            onChange={setTab}
            options={[
              { value: "chart", label: `Chart (${view.chart.length})` },
              { value: "actions", label: "Actions" },
            ]}
          />
        ) : null}
      </View>
      {wide ? (
        <View className="flex-1 flex-row gap-3 px-3">
          <ScrollView
            className="flex-[3]"
            contentContainerClassName="gap-3 pb-6"
          >
            {chart}
          </ScrollView>
          <ScrollView
            className="flex-[2]"
            contentContainerClassName="gap-3 pb-6"
          >
            {panel}
            <Muted>Simulated time moves only when you act or wait.</Muted>
          </ScrollView>
        </View>
      ) : (
        <ScrollView
          className="flex-1"
          contentContainerClassName="gap-3 px-3 pb-6"
        >
          {tab === "chart" ? chart : panel}
        </ScrollView>
      )}
      <Disclaimer />
    </View>
  );
}
