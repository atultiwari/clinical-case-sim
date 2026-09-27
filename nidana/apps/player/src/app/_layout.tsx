import "../global.css";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { Link } from "expo-router";
import { Pressable, Text, View } from "react-native";
import { AccountProvider } from "@/lib/account";
import { GameProvider } from "@/lib/game";

function HeaderLinks() {
  return (
    <View className="flex-row gap-1">
      {(
        [
          ["/profile", "Profile"],
          ["/credits", "Credits"],
        ] as const
      ).map(([href, label]) => (
        <Link key={href} href={href} asChild>
          <Pressable
            testID={`nav-${label.toLowerCase()}`}
            accessibilityRole="link"
            className="min-h-11 justify-center px-3"
          >
            <Text className="font-medium text-brand">{label}</Text>
          </Pressable>
        </Link>
      ))}
    </View>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <GameProvider>
        <AccountProvider>
          <StatusBar style="dark" />
          <Stack
            screenOptions={{
              headerTitleStyle: { fontWeight: "600" },
              headerTintColor: "#1d5c8f",
              contentStyle: { backgroundColor: "#f7f8fa" },
            }}
          >
            <Stack.Screen
              name="index"
              options={{ title: "Nidana", headerRight: () => <HeaderLinks /> }}
            />
            <Stack.Screen
              name="welcome"
              options={{ title: "Welcome to Nidana" }}
            />
            <Stack.Screen name="profile" options={{ title: "Profile" }} />
            <Stack.Screen name="credits" options={{ title: "Credits" }} />
            <Stack.Screen name="case/[slug]" options={{ title: "Case" }} />
            <Stack.Screen
              name="play/[id]/index"
              options={{ title: "Workspace" }}
            />
            <Stack.Screen
              name="play/[id]/commit"
              options={{ title: "Commit" }}
            />
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
        </AccountProvider>
      </GameProvider>
    </SafeAreaProvider>
  );
}
