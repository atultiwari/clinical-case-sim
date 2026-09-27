import type { TrainingLevel } from "@nidana/contracts/api";
import { router } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";
import {
  Button,
  Card,
  Checkbox,
  ErrorNote,
  Muted,
  Screen,
  Tabs,
} from "@/components/ui";
import { TRAINING_LEVELS, nicknameProblem, useAccount } from "@/lib/account";
import { useApi } from "@/lib/game";

/**
 * The consent screen (N1.6; SPEC §8.1, §12). Nothing is sent and no account exists until the
 * player agrees; then the app signs in anonymously and creates the profile.
 */
export default function Welcome() {
  const api = useApi();
  const { setProfile } = useAccount();
  const [nickname, setNickname] = useState("");
  const [level, setLevel] = useState<TrainingLevel>("mbbs_student");
  const [agreed, setAgreed] = useState(false);
  const [research, setResearch] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const problem = nickname.length > 0 ? nicknameProblem(nickname) : null;

  const join = async () => {
    setSaving(true);
    setError(null);
    try {
      const profile = await api.saveMe({
        nickname: nickname.trim(),
        trainingLevel: level,
        consentResearch: research,
        agreed: true,
      });
      setProfile(profile);
      router.replace("/");
    } catch (e: unknown) {
      setError(
        e instanceof Error ? e.message : "Could not create your profile",
      );
      setSaving(false);
    }
  };

  return (
    <Screen>
      <View className="gap-1">
        <Text className="text-2xl font-bold text-ink">Before you play</Text>
        <Muted>
          Nidana is a teaching game built from published case reports. It is in
          development testing.
        </Muted>
      </View>

      <Card testID="consent-terms">
        <Text className="text-base font-semibold text-ink">What is stored</Text>
        <Text className="text-sm leading-5 text-ink">
          A nickname you choose, your training level, and what you do in each
          case: your questions, tests, referrals, diagnosis, plan and score. No
          real name, email or phone number is asked for.
        </Text>
        <Text className="text-base font-semibold text-ink">Who sees it</Text>
        <Text className="text-sm leading-5 text-ink">
          Dr Atul Tiwari, who runs the test, can see play data to improve the
          game. Other players see nothing of yours.
        </Text>
        <Text className="text-base font-semibold text-ink">
          How long it is kept
        </Text>
        <Text className="text-sm leading-5 text-ink">
          Test data is deleted before the game is released in the app stores.
        </Text>
      </Card>

      <Card testID="profile-form">
        <Text className="text-base font-semibold text-ink">Nickname</Text>
        <TextInput
          testID="nickname"
          value={nickname}
          onChangeText={setNickname}
          placeholder="Not your real name"
          autoCorrect={false}
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
      </Card>

      <View className="gap-1">
        <Checkbox
          testID="agree"
          checked={agreed}
          onChange={setAgreed}
          label="I agree to take part in development testing on these terms."
        />
        <Checkbox
          testID="research"
          checked={research}
          onChange={setResearch}
          label="Optional: my playthroughs may be used for research, only with ethics approval and without anything that identifies me."
        />
      </View>

      <ErrorNote message={error} />
      <Button
        testID="join"
        label={saving ? "Joining…" : "Start playing"}
        disabled={
          saving || !agreed || nickname.trim().length === 0 || problem !== null
        }
        onPress={join}
      />
    </Screen>
  );
}
