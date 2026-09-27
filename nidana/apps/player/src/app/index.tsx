import type { EncounterSummary } from "@nidana/contracts/api";
import { Link, Redirect } from "expo-router";
import { Pressable, Text, View } from "react-native";
import {
  Button,
  ErrorNote,
  Heading,
  Loading,
  Muted,
  Screen,
} from "@/components/ui";
import { useAccount } from "@/lib/account";
import { useApi } from "@/lib/game";
import { useLoad } from "@/lib/use-load";

const DIFFICULTY_LABEL = {
  guided: "Guided",
  standard: "Standard",
  expert: "Expert",
} as const;

function MyEncounters({
  encounters,
}: {
  readonly encounters: readonly EncounterSummary[];
}) {
  if (encounters.length === 0) return null;
  return (
    <View testID="my-encounters" className="gap-2">
      <Text className="text-base font-semibold text-ink">My encounters</Text>
      {encounters.map((e) => {
        const done = e.status === "committed";
        return (
          <Link
            key={e.encounterId}
            href={
              done ? `/play/${e.encounterId}/debrief` : `/play/${e.encounterId}`
            }
            asChild
          >
            <Pressable
              testID={`encounter-${e.encounterId}`}
              accessibilityRole="link"
              className="min-h-11 flex-row items-center gap-3 rounded-xl border border-line bg-white px-4 py-3 active:bg-blue-50"
            >
              <View className="flex-1">
                <Text className="text-sm font-medium text-ink">
                  {e.caseTitle}
                </Text>
                <Muted>
                  {DIFFICULTY_LABEL[e.difficulty]} ·{" "}
                  {new Date(e.startedAt).toLocaleDateString("en-GB")}
                </Muted>
              </View>
              <Text
                className={`text-sm font-semibold ${done ? "text-final" : "text-brand"}`}
              >
                {done
                  ? `Score ${Math.round(e.total ?? 0)} · Debrief`
                  : "Continue"}
              </Text>
            </Pressable>
          </Link>
        );
      })}
    </View>
  );
}

function Cases() {
  const api = useApi();
  const { data: cases, error } = useLoad(
    () => api.cases(),
    [api],
    "Could not load the cases",
  );
  const { data: mine } = useLoad(
    () => api.myEncounters(),
    [api],
    "Could not load your encounters",
  );
  return (
    <>
      <ErrorNote message={error} />
      <MyEncounters encounters={mine ?? []} />
      <Text className="text-base font-semibold text-ink">Cases</Text>
      {cases === null && error === null ? (
        <Loading label="Loading cases…" />
      ) : null}
      <View className="gap-3">
        {(cases ?? []).map((c) => (
          <Link key={c.slug} href={`/case/${c.slug}`} asChild>
            <Pressable
              testID={`case-${c.slug}`}
              accessibilityRole="link"
              className="gap-1 rounded-xl border border-line bg-white p-4 active:bg-blue-50"
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
    </>
  );
}

/** Home (SPEC §5.3): the player's encounters and the published cases, neutral titles only (§5.14). */
export default function Home() {
  const { status, profile, error, recheck } = useAccount();
  if (status === "checking") return <Loading />;
  if (status === "needs_consent") return <Redirect href="/welcome" />;
  return (
    <Screen>
      <View className="gap-1">
        <Text className="text-2xl font-bold text-ink">Diagnose real cases</Text>
        <Muted>
          Take a history, examine, order tests at real prices and turnaround,
          then commit to a diagnosis and plan.
        </Muted>
        {profile ? <Muted>Signed in as {profile.nickname}</Muted> : null}
      </View>
      {status === "error" ? (
        <>
          <ErrorNote message={error} />
          <Button label="Try again" onPress={recheck} />
        </>
      ) : (
        <Cases />
      )}
    </Screen>
  );
}
