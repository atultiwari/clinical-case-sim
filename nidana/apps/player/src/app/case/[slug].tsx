import type { Difficulty } from "@nidana/contracts/api";
import { Redirect, router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";
import {
  Button,
  Card,
  ErrorNote,
  Heading,
  Loading,
  Muted,
  Screen,
  Tabs,
} from "@/components/ui";
import { useAccount } from "@/lib/account";
import { useApi } from "@/lib/game";
import { useLoad } from "@/lib/use-load";

const DIFFICULTY: Record<Difficulty, string> = {
  guided:
    "Browse and search; the final report comes first; generous budget; four referrals.",
  standard:
    "Search only; the first film report is provisional and a review can be ordered; three referrals.",
  expert: "As Standard, with a tighter budget and two referrals.",
};

/** The case card (SPEC §5.3): choose a difficulty and start. */
export default function CaseScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const api = useApi();
  const { status } = useAccount();
  const { data: cases, error: loadError } = useLoad(
    () => api.cases(),
    [api],
    "Could not load the case",
  );
  const card = cases?.find((c) => c.slug === slug) ?? null;
  const [difficulty, setDifficulty] = useState<Difficulty>("standard");
  const [startError, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const error = startError ?? loadError;

  const start = async () => {
    setStarting(true);
    setError(null);
    try {
      const view = await api.start({ slug, difficulty });
      router.replace(`/play/${view.encounterId}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Could not start the case");
      setStarting(false);
    }
  };

  if (status === "needs_consent") return <Redirect href="/welcome" />;
  if (cases === null && error === null) return <Loading />;
  return (
    <Screen>
      <ErrorNote message={error} />
      {card ? (
        <Card testID="case-card">
          <Heading>{card.title}</Heading>
          <Muted>{card.tags.join(" · ")}</Muted>
        </Card>
      ) : null}
      <View className="gap-2">
        <Text className="text-base font-semibold text-ink">Difficulty</Text>
        <Tabs
          testID="difficulty"
          value={difficulty}
          onChange={setDifficulty}
          options={[
            { value: "guided", label: "Guided" },
            { value: "standard", label: "Standard" },
            { value: "expert", label: "Expert" },
          ]}
        />
        <Muted>{DIFFICULTY[difficulty]}</Muted>
      </View>
      <Button
        testID="start"
        label={starting ? "Starting…" : "Start the case"}
        disabled={starting || card === null}
        onPress={start}
      />
    </Screen>
  );
}
