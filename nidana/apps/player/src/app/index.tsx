import type { CaseCard } from "@nidana/contracts/api";
import { Link } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, Text, View } from "react-native";
import { ErrorNote, Heading, Loading, Muted, Screen } from "@/components/ui";
import { useApi } from "@/lib/game";

/** Home (SPEC §5.3): the published cases, with neutral titles only (§5.14). */
export default function Home() {
  const api = useApi();
  const [cases, setCases] = useState<CaseCard[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .cases()
      .then(setCases, (e: unknown) =>
        setError(e instanceof Error ? e.message : "Could not load the cases"),
      );
  }, [api]);

  return (
    <Screen>
      <View className="gap-1">
        <Text className="text-2xl font-bold text-ink">Diagnose real cases</Text>
        <Muted>
          Take a history, examine, order tests at real prices and turnaround,
          then commit to a diagnosis and plan.
        </Muted>
      </View>
      <ErrorNote message={error} />
      {cases === null && error === null ? (
        <Loading label="Loading cases…" />
      ) : null}
      <View className="gap-3">
        {(cases ?? []).map((c) => (
          <Link key={c.slug} href={`/case/${c.slug}`} asChild>
            <Pressable
              testID={`case-${c.slug}`}
              accessibilityRole="link"
              className="rounded-xl border border-line bg-white p-4 gap-1 active:bg-blue-50"
            >
              <Heading>{c.title}</Heading>
              <Muted>
                {[c.specialty, ...c.tags.filter((t) => t !== c.specialty)]
                  .filter(Boolean)
                  .join(" · ")}
                {c.estMinutes ? ` · about ${c.estMinutes} min` : ""}
              </Muted>
            </Pressable>
          </Link>
        ))}
      </View>
    </Screen>
  );
}
