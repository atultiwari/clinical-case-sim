import type { ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  View,
} from "react-native";
import { cssInterop } from "nativewind";
import { SafeAreaView } from "react-native-safe-area-context";

// NativeWind styles core components only; third-party ones must be registered to accept className.
cssInterop(SafeAreaView, { className: "style" });

/** Small building blocks shared by the screens. */

export function Disclaimer() {
  return (
    <Text
      testID="disclaimer"
      className="px-4 py-3 text-center text-xs text-muted"
    >
      Nidana is an educational simulation built from published case reports. It
      is not clinical advice.
    </Text>
  );
}

/** A screen: scrolling content with the disclaimer as a fixed footer, visible at all times (SPEC §5.3). */
export function Screen({
  children,
  scroll = true,
}: {
  readonly children: ReactNode;
  readonly scroll?: boolean;
}) {
  return (
    <SafeAreaView
      edges={["bottom", "left", "right"]}
      className="flex-1 bg-paper"
    >
      {scroll ? (
        <ScrollView
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
          className="flex-1"
          contentContainerClassName="p-4 gap-4 max-w-5xl w-full self-center"
        >
          {children}
        </ScrollView>
      ) : (
        <View className="flex-1">{children}</View>
      )}
      <View className="border-t border-line bg-white">
        <Disclaimer />
      </View>
    </SafeAreaView>
  );
}

export function Card({
  children,
  testID,
}: {
  readonly children: ReactNode;
  readonly testID?: string;
}) {
  return (
    <View
      testID={testID}
      className="rounded-xl border border-line bg-white p-4 gap-2"
    >
      {children}
    </View>
  );
}

export function Heading({ children }: { readonly children: ReactNode }) {
  return <Text className="text-lg font-semibold text-ink">{children}</Text>;
}

export function Muted({ children }: { readonly children: ReactNode }) {
  return <Text className="text-sm text-muted">{children}</Text>;
}

interface ButtonProps {
  readonly label: string;
  readonly onPress: () => void;
  readonly testID?: string;
  readonly variant?: "primary" | "secondary" | "danger";
  readonly disabled?: boolean;
}

export function Button({
  label,
  onPress,
  testID,
  variant = "primary",
  disabled = false,
}: ButtonProps) {
  const tone =
    variant === "primary"
      ? "bg-brand"
      : variant === "danger"
        ? "bg-danger"
        : "bg-white border border-line";
  const text = variant === "secondary" ? "text-ink" : "text-white";
  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={label}
      disabled={disabled}
      onPress={onPress}
      className={`rounded-lg px-4 py-2.5 items-center ${tone} ${disabled ? "opacity-40" : ""}`}
    >
      <Text className={`font-medium ${text}`}>{label}</Text>
    </Pressable>
  );
}

export function StatusBadge({
  status,
}: {
  readonly status: "provisional" | "final";
}) {
  const provisional = status === "provisional";
  return (
    <View
      testID={provisional ? "badge-provisional" : "badge-final"}
      className={`self-start rounded-full px-2.5 py-0.5 ${provisional ? "bg-amber-100" : "bg-green-100"}`}
    >
      <Text
        className={`text-xs font-semibold ${provisional ? "text-provisional" : "text-final"}`}
      >
        {provisional ? "Provisional" : "Final"}
      </Text>
    </View>
  );
}

export function ErrorNote({ message }: { readonly message: string | null }) {
  if (message === null) return null;
  return (
    <View
      testID="error"
      className="rounded-lg border border-red-200 bg-red-50 p-3"
    >
      <Text className="text-sm text-danger">{message}</Text>
    </View>
  );
}

export function Loading({ label = "Loading…" }: { readonly label?: string }) {
  return (
    <View className="items-center gap-2 p-8">
      <ActivityIndicator />
      <Muted>{label}</Muted>
    </View>
  );
}

export function Tabs<T extends string>({
  options,
  value,
  onChange,
  testID,
}: {
  readonly options: readonly { readonly value: T; readonly label: string }[];
  readonly value: T;
  readonly onChange: (value: T) => void;
  readonly testID?: string;
}) {
  return (
    <View testID={testID} className="flex-row flex-wrap gap-1.5">
      {options.map((option) => {
        const active = option.value === value;
        return (
          <Pressable
            key={option.value}
            testID={`${testID ?? "tab"}-${option.value}`}
            accessibilityRole="tab"
            accessibilityState={{ selected: active }}
            onPress={() => onChange(option.value)}
            className={`rounded-full px-3 py-1.5 border ${active ? "bg-brand border-brand" : "bg-white border-line"}`}
          >
            <Text
              className={`text-sm ${active ? "text-white font-medium" : "text-ink"}`}
            >
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}
