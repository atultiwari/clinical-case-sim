import "../global.css";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { GameProvider } from "@/lib/game";

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <GameProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerTitleStyle: { fontWeight: "600" },
            headerTintColor: "#1d5c8f",
            contentStyle: { backgroundColor: "#f7f8fa" },
          }}
        >
          <Stack.Screen name="index" options={{ title: "Nidana" }} />
          <Stack.Screen name="case/[slug]" options={{ title: "Case" }} />
          <Stack.Screen
            name="play/[id]/index"
            options={{ title: "Workspace" }}
          />
          <Stack.Screen name="play/[id]/commit" options={{ title: "Commit" }} />
          <Stack.Screen
            name="play/[id]/debrief"
            options={{
              title: "Debrief",
              headerBackVisible: false,
              headerLeft: () => null,
              gestureEnabled: false,
            }}
          />
        </Stack>
      </GameProvider>
    </SafeAreaProvider>
  );
}
