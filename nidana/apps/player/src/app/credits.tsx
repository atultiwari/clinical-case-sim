import { useState } from "react";
import { Text, View } from "react-native";
import * as WebBrowser from "expo-web-browser";
import {
  Button,
  Card,
  ErrorNote,
  Loading,
  Muted,
  Screen,
} from "@/components/ui";
import { useApi } from "@/lib/game";
import { useLoad } from "@/lib/use-load";

/**
 * Credits (SPEC §12): the attribution of every case. Article titles often name the diagnosis,
 * so the list stays hidden until the player asks for it; each debrief also credits its own case.
 */
export default function CreditsScreen() {
  const api = useApi();
  const { data, error } = useLoad(
    () => api.credits(),
    [api],
    "Could not load the credits",
  );
  const [shown, setShown] = useState(false);
  if (data === null) return error ? <ErrorNote message={error} /> : <Loading />;
  return (
    <Screen>
      <Card testID="credits-statement">
        <Text className="text-base font-semibold text-ink">
          Where the cases come from
        </Text>
        <Text className="text-sm leading-5 text-ink">{data.statement}</Text>
        <Muted>
          {data.sources.length} published case reports are used, each under its
          own open licence.
        </Muted>
      </Card>
      {shown ? (
        <View testID="sources" className="gap-2">
          {data.sources.map((s, i) => (
            <Card key={`${s.citation ?? ""}-${i}`}>
              {s.citation ? (
                <Text className="text-sm text-ink">{s.citation}</Text>
              ) : null}
              <Muted>
                Licence: {s.licence}
                {s.attribution ? `. ${s.attribution}` : ""}
              </Muted>
              {s.url && /^https?:\/\//i.test(s.url) ? (
                <Button
                  label="Read the article"
                  variant="secondary"
                  onPress={() => void WebBrowser.openBrowserAsync(s.url ?? "")}
                />
              ) : null}
            </Card>
          ))}
        </View>
      ) : (
        <Card testID="sources-hidden">
          <Text className="text-sm font-medium text-provisional">
            Spoiler warning
          </Text>
          <Muted>
            The article titles often name the diagnosis. Each case&apos;s source
            is also shown in its own debrief.
          </Muted>
          <Button
            testID="show-sources"
            label="Show the sources"
            variant="secondary"
            onPress={() => setShown(true)}
          />
        </Card>
      )}
    </Screen>
  );
}
