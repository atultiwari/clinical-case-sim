import type { TrainingLevel } from "@nidana/contracts/api";
import { Link } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";
import {
  Button,
  Card,
  Checkbox,
  ErrorNote,
  Loading,
  Muted,
  Screen,
  Tabs,
} from "@/components/ui";
import { TRAINING_LEVELS, nicknameProblem, useAccount } from "@/lib/account";
import { useApi } from "@/lib/game";

/** The player's profile (N1.6): nickname, training level and research consent, which can be withdrawn. */
export default function ProfileScreen() {
  const api = useApi();
  const { profile, setProfile } = useAccount();
  const [nickname, setNickname] = useState(profile?.nickname ?? "");
  const [level, setLevel] = useState<TrainingLevel>(
    profile?.trainingLevel ?? "other",
  );
  const [research, setResearch] = useState(profile?.consentResearch ?? false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (profile === null) return <Loading />;
  const problem = nicknameProblem(nickname);

  const save = async () => {
    setError(null);
    setMessage(null);
    try {
      setProfile(
        await api.saveMe({
          nickname: nickname.trim(),
          trainingLevel: level,
          consentResearch: research,
          agreed: true,
        }),
      );
      setMessage("Saved.");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Could not save your profile");
    }
  };

  return (
    <Screen>
      <Card testID="profile">
        <Text className="text-base font-semibold text-ink">Nickname</Text>
        <TextInput
          testID="nickname"
          value={nickname}
          onChangeText={setNickname}
          maxLength={24}
          accessibilityLabel="Nickname"
          className="rounded-lg border border-line bg-white px-3 py-2 text-ink"
        />
        {problem ? (
          <Text className="text-sm text-danger">{problem}</Text>
        ) : null}
        <Text className="text-base font-semibold text-ink">Training level</Text>
        <Tabs
          testID="level"
          value={level}
          onChange={setLevel}
          options={TRAINING_LEVELS}
        />
        <Checkbox
          testID="research"
          checked={research}
          onChange={setResearch}
          label="My playthroughs may be used for research, only with ethics approval and without anything that identifies me."
        />
        <Muted>
          Joined {new Date(profile.joinedAt).toLocaleDateString("en-GB")}
          {profile.role === "admin" ? " · Admin" : ""}
        </Muted>
      </Card>
      <ErrorNote message={error} />
      {message ? <Text className="text-sm text-final">{message}</Text> : null}
      <Button
        testID="save-profile"
        label="Save"
        disabled={problem !== null}
        onPress={save}
      />
      <View className="flex-row gap-2">
        <Link href="/credits" asChild>
          <Button
            label="Credits"
            variant="secondary"
            onPress={() => undefined}
          />
        </Link>
      </View>
    </Screen>
  );
}
